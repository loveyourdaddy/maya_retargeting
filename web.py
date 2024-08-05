from flask import Flask, request, send_file, session, jsonify
import os
import subprocess

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 세션을 사용하기 위해 필요한 비밀키
app.config['UPLOAD_FOLDER'] = './Server_datas/'  # 파일을 저장할 경로
app.config['OUTPUT_FOLDER'] = './output/' # 파일을 불러올 경로
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 파일 크기 제한 (16 MB)

# 업로드 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

# 파일 업로드를 위한 HTML 폼을 제공하는 라우트
@app.route('/')
def upload_form():
    return '''
    <!doctype html>
    <html>
    <head>
        <script>
            function uploadFiles(event) {
                event.preventDefault();
                var formData = new FormData(document.getElementById('uploadForm'));

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);  // Show popup with the result message
                })
                .catch(error => {
                    alert('An error occurred: ' + error.message);
                });
            }

            function downloadFile(event) {
                event.preventDefault();

                fetch('/download', {
                    method: 'POST'
                })
                .then(response => {
                    if (response.ok) {
                        const filename = response.headers.get('X-Filename') || 'downloaded_file'; // Get filename from response headers
                        return response.blob().then(blob => ({ blob, filename }));
                    } else {
                        throw new Error('File not found');
                    }
                })
                .then(({ blob, filename }) => {
                    var link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = filename;
                    link.click();
                })
                .catch(error => {
                    alert('An error occurred: ' + error.message);
                });
            }
        </script>
    </head>
    <body>
        <h1>Upload Files and Retargeting Process</h1>
        <form id="uploadForm" onsubmit="uploadFiles(event)">
            <label for="file1">Target Character:</label><br>
            <input type="file" id="file1" name="file1"><br>
            <label for="file2">Source Character:</label><br>
            <input type="file" id="file2" name="file2"><br>
            <label for="file3">Source Motion:</label><br>
            <input type="file" id="file3" name="file3"><br><br>
            <input type="submit" value="Upload and Process">
        </form>
        <h2>Download a File</h2>
        <form id="downloadForm" onsubmit="downloadFile(event)">
            <input type="submit" value="Download File">
        </form>
    </body>
    </html>
    '''

# 파일 업로드를 처리하는 라우트
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
        return jsonify({'message': 'No file parts'})

    file1 = request.files['file1']
    file2 = request.files['file2']
    file3 = request.files['file3']

    if file1.filename == '' or file2.filename == '' or file3.filename == '':
        return jsonify({'message': 'No selected files'})

    if file1 and file2 and file3:
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
        file3_path = os.path.join(app.config['UPLOAD_FOLDER'], file3.filename)
        file1.save(file1_path)
        file2.save(file2_path)
        file3.save(file3_path)

        # 저장한 파일 경로를 세션에 저장
        session['file1_path'] = file1_path
        session['file3_path'] = file3_path
        
        try:
            result = run_maya_script(file1_path, file2_path, file3_path)
            return jsonify({'message': 'Processing complete. You can download the file.'})
        except Exception as e:
            return jsonify({'message': 'An error occurred: ' + str(e)})

def run_maya_script(target_char, source_char, source_motion):
    maya_executable = "/Applications/Autodesk/maya2024/Maya.app/Contents/MacOS/mayapy"
    script_path = "retargeting_different_axis.py"
    
    command = [
        maya_executable,
        script_path,
        "--targetChar", target_char,
        "--sourceChar", source_char,
        "--sourceMotion", source_motion,
    ]
        
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        raise Exception(process.stderr)
    
    return process.stdout

@app.route('/download', methods=['POST'])
def download_file():
    file1_path = session.get('file1_path')
    file3_path = session.get('file3_path')

    if file1_path and file3_path:
        # Determine the output file path based on the uploaded file
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], file1_path.split('/')[-1].split('.')[0], file3_path.split('/')[-1])
        
        if os.path.exists(file_to_download):
            response = send_file(file_to_download, as_attachment=True)
            #response.headers["X-Filename"] = os.path.basename(file_to_download)  # Custom header for filename
            response.headers["X-Filename"] = file3_path.split('/')[-1]
            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400

# Flask 서버 실행
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)

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

global file1_path, file3_path
file1_path = None
file3_path = None


# 파일 업로드를 위한 HTML 폼을 제공하는 라우트
@app.route('/')
def upload_form():
    return '''
    <!doctype html>
    <html>
    <head>
        <style>
            .container {
                display: flex;
                justify-content: space-between;
                width: 100%;
            }
            .column {
                width: 45%;
            }
            .file-input {
                margin-bottom: 10px;
            }
            .buttons {
                display: flex;
                justify-content: center;
                margin-top: 20px;
            }
            .button {
                margin: 0 10px;
            }
            .center-text {
                text-align: center;
            }
            .radio-group {
                margin-bottom: 10px;
            }
        </style>
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

            function toggleFileInput() {
                var etcOption = document.getElementById('etc');
                var fileInput = document.getElementById('file1');
                fileInput.disabled = !etcOption.checked;
            }
        </script>
    </head>
    <body>
        <h1 class="center-text">Upload Files and Retargeting Process</h1>
        <form id="uploadForm" onsubmit="uploadFiles(event)">
            <div class="container">
                <div class="column">
                    <h2>Source</h2>
                    <label for="file2">Source Character:</label><br>
                    <input type="file" id="file2" name="file2" class="file-input"><br>
                    <label for="file3">Source Motion:</label><br>
                    <input type="file" id="file3" name="file3" class="file-input"><br>
                </div>
                <div class="column">
                    <h2>Target</h2>
                    <div class="radio-group">
                        <label><input type="radio" name="characterSelect" value="Adori" onclick="toggleFileInput()"> Adori</label><br>
                        <label><input type="radio" name="characterSelect" value="Asooni" onclick="toggleFileInput()"> Asooni</label><br>
                        <label><input type="radio" name="characterSelect" value="Bear" onclick="toggleFileInput()"> Bear</label><br>
                        <label><input type="radio" name="characterSelect" value="Roblox" onclick="toggleFileInput()"> Roblox</label><br>
                        <label><input type="radio" id="etc" name="characterSelect" value="ETC" onclick="toggleFileInput()"> ETC (User Upload)</label>
                    </div>
                    <label for="file1">Target Character:</label><br>
                    <input type="file" id="file1" name="file1" class="file-input" disabled><br>
                </div>
            </div>
            <div class="buttons">
                <input type="submit" value="Upload and Process" class="button">
            </div>
        </form>
        <h2 class="center-text">Download a File</h2>
        <form id="downloadForm" onsubmit="downloadFile(event)">
            <div class="buttons">
                <input type="submit" value="Download File" class="button">
            </div>
        </form>
    </body>
    </html>
    '''

# 파일 업로드를 처리하는 라우트
@app.route('/upload', methods=['POST'])
def upload_file():
    global file1_path, file3_path
    character_select = request.form.get('characterSelect')

    # 'ETC'가 선택되지 않은 경우 해당 캐릭터의 파일 경로 설정
    if character_select != "ETC":
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{character_select}.fbx")
    else:
        if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
            return jsonify({'message': 'No file parts'})

        file1 = request.files['file1']
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file1.save(file1_path)

    file2 = request.files['file2']
    file3 = request.files['file3']

    if file2.filename == '' or file3.filename == '':
        return jsonify({'message': 'No selected files'})

    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
    file3_path = os.path.join(app.config['UPLOAD_FOLDER'], file3.filename)
    file2.save(file2_path)
    file3.save(file3_path)

    # 저장한 파일 경로를 세션에 저장
    session['file1_path'] = file1_path
    session['file3_path'] = file3_path
    print("here")
    
    try:
        print("run")
        result = run_maya_script(file1_path, file2_path, file3_path)
        return jsonify({'message': 'Processing complete. You can download the file.'})
    except Exception as e:
        print("error")
        return jsonify({'message': 'An error occurred: ' + str(e)})


def run_maya_script(target_char, source_char, source_motion):
    # mac 
    # maya_executable = "/Applications/Autodesk/maya2025/Maya.app/Contents/MacOS/mayapy"
    
    # window 
    maya_executable = "C:\\Program Files\\Autodesk\\Maya2025\\bin\\mayapy" # C:\Program Files\Autodesk\Maya2025\bin\
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
            # response.headers["X-Filename"] = os.path.basename(file_to_download)  # Custom header for filename
            response.headers["X-Filename"] = file3_path.split('/')[-1]
            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400


@app.route('/download_api', methods=['POST'])
def download_file_api():
    
    global file1_path, file3_path

    if file1_path and file3_path:
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], file1_path.split('/')[-1].split('.')[0], file3_path.split('/')[-1])

        if os.path.exists(file_to_download):
            response = send_file(file_to_download, as_attachment=True)
            response.headers["X-Filename"] = file3_path.split('/')[-1]
            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400
    

# Flask 서버 실행
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
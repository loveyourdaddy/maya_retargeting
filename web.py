from flask import Flask, request, send_file, session, jsonify
import os
import subprocess

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 세션을 사용하기 위해 필요한 비밀키
app.config['UPLOAD_FOLDER'] = './Server_datas/'  # 파일을 저장할 경로
app.config['OUTPUT_FOLDER'] = './output/' # 파일을 불러올 경로
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 파일 크기 제한 (16 MB)


# 업로드 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

# key: tranaction_id, value: file1_path, file3_path
transactions = {}

# 파일 업로드를 위한 HTML 폼을 제공하는 라우트
@app.route('/')
def upload_form():
    print("upload form")
    return '''
    <!doctype html>
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .step {
                border: 2px solid #000;
                border-radius: 20px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .step-title {
                font-weight: bold;
                font-size: 1.2em;
                margin-bottom: 10px;
            }
            .file-input {
                margin-bottom: 10px;
            }
            .radio-group {
                margin-bottom: 10px;
            }
            .button {
                display: block;
                width: 100%;
                padding: 10px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                cursor: pointer;
            }
            #processingPopup {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 20px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                z-index: 1000;
            }
        </style>
        <script>
            // JavaScript functions remain the same as in the original code
            function showProcessingPopup() {
                document.getElementById('processingPopup').style.display = 'block';
            }

            function hideProcessingPopup() {
                document.getElementById('processingPopup').style.display = 'none';
            }

            function uploadFiles(event) {
                event.preventDefault();
                var formData = new FormData(document.getElementById('uploadForm'));

                showProcessingPopup();

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    hideProcessingPopup();
                    alert(data.message);
                })
                .catch(error => {
                    hideProcessingPopup();
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
                        const filename = response.headers.get('X-Filename') || 'downloaded_file';
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
        <h1>Danstruct AI Motion System</h1>
        <h2>Upload Files and Retargeting Process</h2>
        <div id="processingPopup">Processing... Please wait.</div>
        <form id="uploadForm" enctype="multipart/form-data" onsubmit="uploadFiles(event)">
            <div class="step">
                <div class="step-title">STEP 1: Source</div>
                <label for="file2">Source Character:</label><br>
                <input type="file" id="file2" name="file2" class="file-input"><br>
                <label for="file3">Source Motion:</label><br>
                <input type="file" id="file3" name="file3" class="file-input"><br>
            </div>
            <div class="step">
                <div class="step-title">STEP 2: Target</div>
                <div class="radio-group">
                    <label><input type="radio" name="characterSelect" value="Adori" onclick="toggleFileInput()"> Adori</label><br>
                    <label><input type="radio" name="characterSelect" value="Asooni" onclick="toggleFileInput()"> Asooni</label><br>
                    <label><input type="radio" name="characterSelect" value="Bear" onclick="toggleFileInput()"> Bear</label><br>
                    <label><input type="radio" name="characterSelect" value="Roblox" onclick="toggleFileInput()"> Roblox</label><br>
                    <label><input type="radio" id="etc" name="characterSelect" value="ETC" onclick="toggleFileInput()"> ETC (User Upload)</label>
                </div>
                <label for="file1">Target Character:</label><br>
                <input type="file" id="file1" name="file1" class="file-input" disabled><br>
                <input type="submit" value="Upload and Process" class="button">
            </div>
        </form>
        <div class="step">
            <div class="step-title">STEP 3: Download a File</div>
            <form id="downloadForm" onsubmit="downloadFile(event)">
                <input type="submit" value="Download File" class="button">
            </form>
        </div>
    </body>
    </html>
    '''

# 파일 업로드를 처리하는 라우트
@app.route('/upload', methods=['POST'])
def upload_file():
    character_select = request.form.get('characterSelect')

    # 'ETC'가 선택되지 않은 경우 해당 캐릭터의 파일 경로 설정
    if character_select != "ETC":
        # print("selected: ", file1_path)
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{character_select}.fbx")
    else:
        # print("etc: ")
        if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
            print("error: no file")
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
    # print("target char", file1_path)
    # print("source char", file3_path)
    
    try:
        print("run")
        result = run_maya_script(file1_path, file2_path, file3_path)
        print(result)
        return jsonify({'message': 'Processing complete. You can download the file.'})
    except Exception as e:
        print("error")
        return jsonify({'message': 'An error occurred: ' + str(e)})

@app.route('/upload_api', methods=['POST'])
def upload_file_api():
    global file1_path, file3_path
    # print("here1")
    if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
        return jsonify({'message': 'No file parts'})

    file1 = request.files['file1'] # target char 
    file2 = request.files['file2'] # source char-
    file3 = request.files['file3'] # source motion 

    if file1.filename == '' or file2.filename == '' or file3.filename == '':
        return jsonify({'message': 'No selected files'})

    if file1 and file2 and file3:
        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
        file3_path = os.path.join(app.config['UPLOAD_FOLDER'], file3.filename)
        file1.save(file1_path)
        file2.save(file2_path)
        file3.save(file3_path)

        # transaction_id 생성
        import uuid
        transaction_id = str(uuid.uuid4())
        print("transaction_id in upload:", transaction_id)
        # transaction_folder = os.path.join(app.config['UPLOAD_FOLDER'], transaction_id)

        # 저장한 파일 경로를 세션에 저장
        transactions[transaction_id] = {
            'file1_path': file1_path,
            'file2_path': file2_path,
            'file3_path': file3_path,
        }
        
        try:
            print("run")
            result = run_maya_script(file1_path, file2_path, file3_path)
            return jsonify({'message': 'Processing complete. You can download the file.', 'transaction_id': transaction_id})
        except Exception as e:
            print("error")
            return jsonify({'message': 'An error occurred: ' + str(e)})

import shutil
def run_maya_script(target_char_path, source_char_path, source_motion_path):
    import platform
    if platform.system() == "Windows":
        maya_executable = "C:\\Program Files\\Autodesk\\Maya2025\\bin\\mayapy" 
    elif platform.system() == "Darwin": # mac 
        maya_executable = "/Applications/Autodesk/maya2025/Maya.app/Contents/MacOS/mayapy"
    else:
        print("Unsupported OS")
        return

    # window 
    script_path = "retargeting_different_axis.py"
    target_char = target_char_path.split('/')[-1][:-len('.fbx')]
    source_char = source_char_path.split('/')[-1][:-len('.fbx')]
    source_motion = source_motion_path.split('/')[-1][:-len('.fbx')]
    print(f"Retargetring: source_char {source_char} source_motion {source_motion} -> target_char {target_char}")

    # mkdir 
    os.makedirs('./models/' + target_char + '/', exist_ok=True)
    os.makedirs('./models/' + source_char + '/', exist_ok=True)
    os.makedirs('./motions/' + source_char + '/', exist_ok=True)

    # target path
    path_target_char = './models/' + target_char + '/'+ target_char + '.fbx'
    path_source_char = './models/' + source_char + '/'+ source_char + '.fbx'
    path_source_motion = './motions/' + source_char + '/' + source_motion + '.fbx'
    
    shutil.copy(target_char_path, path_target_char)
    shutil.copy(source_char_path, path_source_char)
    shutil.copy(source_motion_path, path_source_motion)

    import datetime
    print("Date: ", datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

    command = [
        maya_executable,
        script_path,
        "--targetChar", path_target_char,
        "--sourceChar", path_source_char,
        "--sourceMotion", path_source_motion,
    ]
    print("command:", command)
    process = subprocess.run(command, capture_output=True, text=True)
    print("retargeting end")
    if process.returncode != 0:
        print("Error on run maya script")
        raise Exception(process.stderr)
        
    return process.stdout

@app.route('/download', methods=['POST'])
def download_file():
    file1_path = session.get('file1_path')
    file3_path = session.get('file3_path')
    print("target char", file1_path)
    print("source char", file3_path)

    if file1_path and file3_path:
        # Determine the output file path based on the uploaded file
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], file1_path.split('/')[-1].split('.')[0], file3_path.split('/')[-1])
        print(file_to_download)
        
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
    # Get the transaction ID from the request data
    data = request.json
    transaction_id = data.get('transaction_id')
    # print("transaction_id in download:", transaction_id)

    if not transaction_id or transaction_id not in transactions:
        return jsonify({'message': 'Invalid transaction ID'}), 400

    transaction = transactions[transaction_id]
    file1_path = transaction['file1_path']
    file3_path = transaction['file3_path']

    # load 
    if file1_path and file3_path:
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], file1_path.split('/')[-1].split('.')[0], file3_path.split('/')[-1])

        if os.path.exists(file_to_download):
            response = send_file(file_to_download, as_attachment=True)
            response.headers["X-Filename"] = file3_path.split('/')[-1]
            print("download end")
            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400
    

# Flask 서버 실행
if __name__ == "__main__":
    # app.run(host='127.0.0.1', port=5000, debug=True) # local
    app.run(host='0.0.0.0', port=5000, debug=True) # all interface
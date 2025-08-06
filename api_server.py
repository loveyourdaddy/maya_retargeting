from flask import Flask, request, send_file, session, jsonify
import os
import subprocess
import time 

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 세션을 사용하기 위해 필요한 비밀키
app.config['UPLOAD_FOLDER'] = './Server_datas/'  # 파일을 저장할 경로
app.config['OUTPUT_FOLDER'] = './output/' # 파일을 불러올 경로
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 파일 크기 제한 (1024 MB)
is_remove = True # False

# 업로드 폴더가 없으면 생성
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

# key: tranaction_id, value: target_character, source_character, source_motion
transactions = {}

# 업로드된 임시 파일들을 정리하는 함수
preserved_characters = ['Adori', 'Asooni', 'Bear', 'Roblox']
def cleanup_files(file_paths):
    for file_path in file_paths:
        try:
            # 파일 이름에서 확장자를 제외한 부분 추출
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]

            # 보존할 캐릭터가 아닌 경우에만 삭제
            if name_without_ext not in preserved_characters:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

# Maya 작업 후 생성된 파일들을 정리하는 함수
def cleanup_maya_files(target_char, source_char, source_motion):
    try:
        # models 폴더 정리
        if target_char not in preserved_characters:
            if os.path.exists(f'./models/{target_char}'):
                shutil.rmtree(f'./models/{target_char}')
                print(f"Removed model directory: ./models/{target_char}")
                
        if source_char not in preserved_characters:
            if os.path.exists(f'./models/{source_char}'):
                shutil.rmtree(f'./models/{source_char}')
                print(f"Removed model directory: ./models/{source_char}")
        
            # motions 폴더 정리
            if os.path.exists(f'./motions/{source_char}'):
                shutil.rmtree(f'./motions/{source_char}')
                print(f"Removed model directory: ./motions/{source_char}")
            
        # print(f"Cleaned up Maya working directories")
    except Exception as e:
        print(f"Error cleaning up Maya files: {e}")

''' upload '''
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
                var fileInput = document.getElementById('target_character');
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
                <label for="source_character">Source Character:</label><br>
                <input type="file" id="source_character" name="source_character" class="file-input"><br>
                <label for="source_motion">Source Motion:</label><br>
                <input type="file" id="source_motion" name="source_motion" class="file-input"><br>
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
                <label for="target_character">Target Character:</label><br>
                <input type="file" id="target_character" name="target_character" class="file-input" disabled><br>
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
    uploaded_files = []  # 업로드된 파일 경로 추적

    # 'ETC'가 선택되지 않은 경우 해당 캐릭터의 파일 경로 설정
    if character_select != "ETC":
        target_character_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{character_select}.fbx")
    else:
        if 'target_character' not in request.files or 'source_character' not in request.files or 'source_motion' not in request.files:
            print("error: no file")
            return jsonify({'message': 'No file parts'})

        target_character = request.files['target_character']
        target_character_path = os.path.join(app.config['UPLOAD_FOLDER'], target_character.filename)
        target_character.save(target_character_path)
        uploaded_files.append(target_character_path)

    source_character = request.files['source_character']
    source_motion = request.files['source_motion']

    if source_character.filename == '' or source_motion.filename == '':
        if is_remove:
            cleanup_files(uploaded_files)
        return jsonify({'message': 'No selected files'})

    source_character_path = os.path.join(app.config['UPLOAD_FOLDER'], source_character.filename)
    source_motion_path = os.path.join(app.config['UPLOAD_FOLDER'], source_motion.filename)
    source_character.save(source_character_path)
    source_motion.save(source_motion_path)
    uploaded_files.extend([source_character_path, source_motion_path])

    # 저장한 파일 경로를 세션에 저장
    session['target_character_path'] = target_character_path
    session['source_motion_path'] = source_motion_path
    
    try:
        print("run")
        result = run_maya_script(target_character_path, source_character_path, source_motion_path)
        print("Result:", result)

        # Maya 작업 완료 후 임시 파일 정리 
        if is_remove:
            cleanup_files(uploaded_files)
            cleanup_maya_files(
                target_character_path.split('/')[-1][:-4],
                source_character_path.split('/')[-1][:-4],
                source_motion_path.split('/')[-1][:-4]
            )

        return jsonify({'message': 'Processing complete. You can download the file.'})
    except Exception as e:
        print(">>> run_maya_script Failed")
        if is_remove:
            cleanup_files(uploaded_files)
        return jsonify({'message': 'An error occurred: ' + str(e)})

@app.route('/upload_api', methods=['POST'])
def upload_file_api():
    uploaded_files = []
    global target_character_path, source_motion_path

    if 'target_character' not in request.files or 'source_character' not in request.files or 'source_motion' not in request.files:
        return jsonify({'message': 'No file parts'})

    target_character = request.files['target_character'] # target_character
    source_character = request.files['source_character'] # source_character
    source_motion = request.files['source_motion'] # source_motion 

    if target_character.filename == '' or source_character.filename == '' or source_motion.filename == '':
        return jsonify({'message': 'No selected files'})

    if target_character and source_character and source_motion:
        # Path
        target_character_path = os.path.join(app.config['UPLOAD_FOLDER'], target_character.filename)
        source_character_path = os.path.join(app.config['UPLOAD_FOLDER'], source_character.filename)
        source_motion_path = os.path.join(app.config['UPLOAD_FOLDER'], source_motion.filename)

        # save 
        target_character.save(target_character_path)
        source_character.save(source_character_path)
        source_motion.save(source_motion_path)
        uploaded_files.extend([target_character_path, source_character_path, source_motion_path])

        # transaction_id 생성
        import uuid
        transaction_id = str(uuid.uuid4())
        print("transaction_id in upload:", transaction_id)

        # 저장한 파일 경로를 세션에 저장
        transactions[transaction_id] = {
            'target_character_path': target_character_path,
            'source_character_path': source_character_path,
            'source_motion_path': source_motion_path,
        }
        
        try:
            print("run")
            result = run_maya_script(target_character_path, source_character_path, source_motion_path)

            # Maya 작업 완료 후 임시 파일 정리
            if is_remove:
                cleanup_files(uploaded_files)
                cleanup_maya_files(
                    target_character_path.split('/')[-1][:-4],
                    source_character_path.split('/')[-1][:-4],
                    source_motion_path.split('/')[-1][:-4]
                )

            return jsonify({'message': 'Processing complete. You can download the file.', 'transaction_id': transaction_id})
        except Exception as e:
            print(">>> run_maya_script Failed")
            cleanup_files(uploaded_files)
            return jsonify({'message': 'An error occurred: ' + str(e)})

''' run maya script '''
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

    # path
    script_path = "run_retargeting.py" # retargeting_different_axis
    target_char = target_char_path.split('/')[-1][:-len('.fbx')]
    source_char = source_char_path.split('/')[-1][:-len('.fbx')]
    # source motion
    source_motion_format = source_motion_path.split('/')[-1].split('.')[-1]
    source_motion = source_motion_path.split('/')[-1][:-4]
    
    print(f"Retargetring: source_char {source_char} source_motion {source_motion} -> target_char {target_char}")

    # mkdir 
    os.makedirs('./models/' + target_char + '/', exist_ok=True)
    os.makedirs('./models/' + source_char + '/', exist_ok=True)
    os.makedirs('./motions/' + source_char + '/', exist_ok=True)

    # target path
    path_target_char = './models/' + target_char + '/'+ target_char + '.fbx'
    path_source_char = './models/' + source_char + '/'+ source_char + '.fbx'    
    path_source_motion = './motions/' + source_char + '/'+ source_motion + '.' + source_motion_format
    
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

    # Retargeting
    start_time = time.time()
    process = subprocess.run(command, capture_output=True, text=True)
    # end time 
    end_time = time.time()
    execution_time = end_time - start_time
    print("Retargeting end. execution_time: ", execution_time)

    if process.returncode != 0:
        print("Error on run maya script")
        raise Exception(process.stderr)
        
    return process.stdout

''' download '''
@app.route('/download', methods=['POST'])
def download_file():
    target_character_path = session.get('target_character_path')
    source_motion_path = session.get('source_motion_path')
    print("target char", target_character_path)
    print("source char", source_motion_path)

    if target_character_path and source_motion_path:
        # Determine the output file path based on the uploaded file
        target_char_name = target_character_path.split('/')[-1][:-len('.fbx')] # .split('.')[0]
        output_motion_name = source_motion_path.split('/')[-1].split('.')[0]+'.fbx'
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], target_char_name, output_motion_name)
        print("file_to_download:", file_to_download)
        
        if os.path.exists(file_to_download):
            response = send_file(file_to_download, as_attachment=True)
            response.headers["X-Filename"] = source_motion_path.split('/')[-1]

            # 다운로드 후 output 폴더의 파일 정리 
            try:
                output_file = os.path.join(app.config['OUTPUT_FOLDER'], target_char_name, output_motion_name)
                if os.path.exists(output_file) and is_remove:
                    os.remove(output_file)

            except Exception as e:
                print(f"Error cleaning up output directory: {e}")

            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400

def is_file_in_use(file_path):
    """파일이 사용 중인지 확인하는 함수"""
    try:
        # 쓰기 모드로 파일을 열어보려고 시도 (Windows에서 효과적)
        with open(file_path, 'r+') as f:
            pass  # 파일을 열고 바로 닫음
        return False  # 정상적으로 열리면 사용 중이 아님
    except IOError:
        return True  # 파일을 열 수 없으면 사용 중임
    
@app.route('/download_api', methods=['POST'])
def download_file_api():
    # Get the transaction ID from the request data
    data = request.json
    transaction_id = data.get('transaction_id')

    if not transaction_id or transaction_id not in transactions:
        return jsonify({'message': 'Invalid transaction ID'}), 400

    transaction = transactions[transaction_id]
    target_character_path = transaction['target_character_path']
    source_motion_path = transaction['source_motion_path']

    # load 
    if target_character_path and source_motion_path:
        target_char_name = target_character_path.split('/')[-1][:-len('.fbx')] # .split('.')[0]
        output_motion_name = source_motion_path.split('/')[-1].split('.')[0]+'.fbx'
        file_to_download = os.path.join(app.config['OUTPUT_FOLDER'], target_char_name, output_motion_name)
        print("file_to_download:", file_to_download)

        if os.path.exists(file_to_download):
            response = send_file(file_to_download, as_attachment=True)
            response.headers["X-Filename"] = output_motion_name 
            print("download end")

            # 다운로드 후 output 폴더의 파일 정리 
            try:
                output_file = os.path.join(app.config['OUTPUT_FOLDER'], target_char_name, output_motion_name)
                if os.path.exists(output_file) and is_remove and not is_file_in_use(output_file):
                    os.remove(output_file)
                    
                # transaction 정리
                del transactions[transaction_id]
            except Exception as e:
                print(f"Error cleaning up output directory: {e}")

            return response
        else:
            return jsonify({'message': 'File not found'}), 404
    else:
        return jsonify({'message': 'No file paths available for download'}), 400


# Flask 서버 실행
if __name__ == "__main__":
    # app.run(host='127.0.0.1', port=5000, debug=True) # local 
    app.run(host='0.0.0.0', port=5000, debug=True) # all interface

import os
import io
import pickle
import streamlit as st
import google.generativeai as genai
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaByteArrayUpload, MediaIoBaseDownload

# ==========================================
# 1. إعدادات الموديل ومفتاح الـ API الخاص بكِ
# ==========================================

# تم وضع مفتاح الـ API الخاص بكِ هنا مباشرة لتشغيل عقل ميلا
GEMINI_API_KEY = "AQ.Ab8RN6Kc8Idh9PT1p09zaIQFM6dB9JMfAcznA"
genai.configure(api_key=GEMINI_API_KEY)

# اختيار نسخة جيميناي المتطورة للمحادثات ذات الذاكرة
model = genai.GenerativeModel('gemini-1.5-pro')

SCOPES = ['https://www.googleapis.com/auth/drive.file']
PASSWORD_FILE_NAME = "mila_password.txt"

# ==========================================
# 2. الاتصال بالسحابة (Google Drive)
# ==========================================

def get_drive_service():
    """الاتصال الآمن بحساب الجيميل الخاص بميلا والوصول للدرايف"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def get_current_password_from_drive(service):
    """جلب كلمة السر الحالية المخزنة في جوجل درايف"""
    query = f"name = '{PASSWORD_FILE_NAME}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        default_password = "mila_default_pass"
        file_metadata = {'name': PASSWORD_FILE_NAME}
        media = MediaByteArrayUpload(default_password.encode('utf-8'), mimetype='text/plain')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id'), default_password
    else:
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        current_password = fh.getvalue().decode('utf-8').strip()
        return file_id, current_password

# ==========================================
# 3. منطق الأمان وتعديل كلمة السر
# ==========================================

def change_password_logic(service, old_input, new_input):
    """التحقق من الرمز القديم أولاً ثم استبداله بالجديد في السحابة"""
    file_id, real_old_password = get_current_password_from_drive(service)
    
    if old_input != real_old_password:
        return False, "الرمز القديم غير صحيح! ميلا لم تتعرف عليكِ."
    
    if not new_input:
        return False, "الرجاء إدخال الرمز الجديد."
        
    # تحديث الملف على السحابة (جوجل درايف) مباشرة
    media = MediaByteArrayUpload(new_input.encode('utf-8'), mimetype='text/plain')
    service.files().update(fileId=file_id, media_body=media).execute()
    return True, "تم تعديل الرمز بنجاح واعتماده في سحابة ميلا!"

# ==========================================
# 4. إدارة عقل ومحادثات ميلا (Gemini Chat)
# ==========================================

def init_mila_brain():
    """تفعيل عقل ميلا وضمان وجود ذاكرة مستمرة للمحادثة"""
    if "mila_chat" not in st.session_state:
        system_instruction = (
            "أنتِ 'ميلا'، المساعدة الشخصية الذكية والوفية. "
            "تتميزين بالذكاء الشديد، ولديكِ ذاكرة قوية تتذكر تفاصيل المستخدم بدقة. "
            "تتحدثين بلهجة ودية، ذكية، ومباشرة."
        )
        st.session_state.mila_chat = model.start_chat(history=[])
        st.session_state.mila_history = [
            {"role": "mila", "content": "مرحباً بكِ! أنا ميلا، عقلي متصل وجاهز لمساعدتكِ في أي وقت."}
        ]

def ask_mila(user_message):
    """إرسال الرسالة إلى عقل ميلا واستقبال الرد"""
    try:
        response = st.session_state.mila_chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"حدث خطأ في الاتصال بعقلي: {str(e)}"

# ==========================================
# 5. واجهة المستخدم والتصميم (Streamlit UI)
# ==========================================

st.set_page_config(page_title="Mila AI", page_icon="🤖", layout="centered")
st.title("🤖 تطبيق ميلا الشخصي - Mila AI")

# تهيئة عقل ميلا
init_mila_brain()

# محاولة الاتصال بالدرايف لإدارة الأمان
try:
    drive_service = get_drive_service()
except Exception as e:
    st.error("الرجاء التأكد من وجود ملف credentials.json لإتمام الاتصال بالسحابة.")
    drive_service = None

# القائمة الجانبية لإدارة الأمان وتغيير الرمز
with st.sidebar:
    st.header("🔐 إعدادات الأمان")
    st.subheader("تغيير رمز المرور الخاص بميلا")
    
    old_pass_input = st.text_input("أدخلي الرمز القديم:", type="password")
    new_pass_input = st.text_input("أدخلي الرمز الجديد:", type="password")
    
    if st.button("تأكيد وتغيير الرمز"):
        if drive_service:
            success, message = change_password_logic(drive_service, old_pass_input, new_pass_input)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.error("لا يمكن تغيير الرمز حالياً لعدم الاتصال بالسحابة.")

# عرض تاريخ المحادثة
st.subheader("💬 المحادثة")
for msg in st.session_state.mila_history:
    if msg["role"] == "user":
        st.write(f"**أنتِ:** {msg['content']}")
    else:
        st.write(f"**ميلا:** {msg['content']}")

# صندوق إدخال الرسائل الجديد
user_input = st.text_input("تحدثي مع ميلا...", key="user_say")

if st.button("إرسال") and user_input:
    # حفظ رسالة المستخدم
    st.session_state.mila_history.append({"role": "user", "content": user_input})
    
    # جلب الرد من عقل ميلا
    with st.spinner("ميلا تفكر..."):
        mila_response = ask_mila(user_input)
    
    # حفظ رد ميلا وعرضه
    st.session_state.mila_history.append({"role": "mila", "content": mila_response})
    st.rerun()

import streamlit as st
import time

# 1. إعدادات واجهة التطبيق
st.set_page_config(page_title="Mila Assistant", page_icon="🔮", layout="centered")

# إعداد الحالة الأولية للأمان في المتصفح
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 2. دالة الأمان الذكية (الربط الديناميكي بالدرايف)
# هادي الدالة حتقرأ الباسورد وحالة الجلسة من السحابة مباشرة
def check_security_status():
    try:
        # لما نربطوا الـ Secrets بعد شوية، حيقرا القيم الحقيقية من الدرايف متعكِ
        correct_password = st.secrets.get("MILA_PASSWORD", "Mila_2026")
        is_session_active = st.secrets.get("SESSION_ACTIVE", True)
        return correct_password, is_session_active
    except Exception:
        # الافتراضي الاحتياطي عشان التطبيق ما يكرشش في أول تشغيل
        return "Mila_2026", True

correct_password, is_session_active = check_security_status()

# 🎯 ميزة الطرد الفوري عن بُعد اللي طلبتيها:
# لو تم إلغاء تفعيل الجلسة من جهاز ثاني، التطبيق حيفصل تلقائياً ويمسح الشاشة
if not is_session_active and st.session_state["authenticated"]:
    st.session_state["authenticated"] = False
    st.warning("🔴 تم إنهاء هذه الجلسة عن بُعد لدواعي الأمان. جاري قفل الشاشة...")
    time.sleep(2)
    st.rerun()

# 3. نظام شاشة القفل (Lock Screen)
if not st.session_state["authenticated"]:
    st.title("🔒 شاشة الأمان | مـيـلا")
    st.subheader("مرحباً بكِ يا أروى، يرجى توثيق الهوية للوصول للمساعد الذكي.")
    
    password_input = st.text_input("أدخلي كلمة المرور الديناميكية:", type="password")
    
    if st.button("تسجيل الدخول"):
        if password_input == correct_password:
            st.session_state["authenticated"] = True
            st.success("تم التوثيق بنجاح! جاري فتح ميلا...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("كلمة المرور غير صحيحة! حاولي مجدداً.")

# 4. واجهة المحادثة وميلا الشغالة (بعد كتابة الباسورد الصح)
else:
    st.title("🔮 ميلا | المساعد الشخصي الذكي")
    
    # 🛡️ لوحة التحكم بالأمان الفوري (Kill-Switch UI)
    with st.sidebar:
        st.header("⚙️ مركز الأمان")
        st.write("تحكمي في جلسات ميلا من هنا:")
        
        if st.button("🚨 طرد وإغلاق الجلسات الأخرى فوراً"):
            st.toast("جاري إرسال أمر الطرد الفوري لجوجل درايف... 🤫")
            # هنا الكود حيتعدل بعدين ليكتب في ملف الدرايف لقطع الاتصال عن باقي الأجهزة
            
        if st.button("🚪 تسجيل الخروج من هذا الجهاز"):
            st.session_state["authenticated"] = False
            st.rerun()
            
        st.markdown("---")
        st.caption("مشروع تخرج - تأثير برنامج جيوجيبرا على تحصيل الطلاب")

    # صندوق عرض الرسائل والشات
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "مرحبتين بيكِ يا أروى! أنا ميلا، ومستعدة لمساعدتكِ اليوم في مشروع التخرج أو في أي شيء تبيه. شن عندنا؟"}]

    # عرض التاريخ القديم للمحادثة الحالية على الشاشة
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # استقبال رسايلكِ الجديدة
    if prompt := st.chat_input("تحدثي مع ميلا..."):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # استدعاء محرك الذكاء والذاكرة (ح نفعلوه بالكامل بمجرد ربط مفتاح الـ API)
        with st.chat_message("assistant"):
            reply = f"أنا معكِ وسجلت كلامكِ! بمجرد ما نربطوا مفتاح الـ API والذاكرة في الخطوة الجاية، حنردوا بالذكاء الكامل."
            st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

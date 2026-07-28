import streamlit as st


def show_employee_panel():

    st.subheader("My Account")

    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Username", value=user["username"], disabled=True)
        st.text_input("Role", value=user["role"].capitalize(), disabled=True)

    with col2:
        st.text_input("Full Name", value=user.get("full_name", ""), disabled=True)
        st.text_input("Email", value=user.get("email", ""), disabled=True)

    st.success("Account Status : Active")

    st.markdown("---")

    st.markdown("### Available Features")

    st.markdown("""
- ✅ AI Chat Assistant
- ✅ Company Knowledge Search (RAG)
- ✅ Company Documents
- ✅ Email Assistant *(coming soon)*
- ✅ Calendar Assistant *(coming soon)*
- ✅ Report Generation *(coming soon)*
- ✅ Database Query Assistant *(coming soon)*
""")

    st.info("If you require additional permissions, please contact your manager.")
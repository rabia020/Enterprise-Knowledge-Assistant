from tools.n8n_client import (
    send_email,
  
    test_connection
)

# Check n8n is running
print("Health Check:", test_connection())

print("\nTesting Email...")

success = send_email(
    to="your_email@gmail.com",
    subject="Test Email",
    body="This is a test from AI system"
)

print("Email Result:", success)

"""# 3. Test Slack
print("\nTesting Slack...")
send_slack_message(
    channel="#general",
    message="Slack integration working ✅"
)

# 4. Test Jira
print("\nTesting Jira...")
create_jira_ticket(
    summary="Test Bug from AI System",
    description="This is a test ticket",
    priority="Low"
)

# 5. Test Calendar
print("\nTesting Calendar...")
create_calendar_event(
    title="AI Test Meeting",
    date="2026-01-01",
    description="Testing calendar integration"
)"""
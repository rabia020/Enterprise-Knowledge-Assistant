from tools.n8n_client import (
    send_email,
    send_slack_message,
    create_calendar_event,
    create_jira_ticket,
    send_rag_query
)


# ==========================================================
# EXECUTOR
# ==========================================================

def executor(state):

    print("[Executor] Running...")


    # SAFETY CHECK
    # ------------------------------------------------------

    if state.get("approved") is not True:

        print(
            "[Executor] Actions not approved. "
            "Skipping execution."
        )


        return {

            "tool_results": [

                {

                    "status": "skipped",

                    "message": (
                        "Actions were not approved."
                    )

                }

            ],

            "messages": [

                "[Executor] Execution skipped — not approved"

            ],

            "status": "skipped"

        }


    tool_calls = state.get(
        "tool_calls",
        []
    )


    results = []


    for call in tool_calls:

        tool = call.get("tool")

        args = call.get(
            "args",
            {}
        )


        print(
            f"[Executor] Tool → {tool}"
        )

        print(
            f"[Executor] Args → {args}"
        )


        result = None


        # ==================================================
        # EMAIL
        # ==================================================

        if tool == "SendEmail_Tool":

            result = send_email(

                to=args.get(
                    "to",
                    ""
                ),

                subject=args.get(
                    "subject",
                    "Enterprise Assistant Update"
                ),

                body=args.get(
                    "message",
                    ""
                )

            )


        # ==================================================
        # SLACK
        # ==================================================

        elif tool == "Send_Slack":

            result = send_slack_message(

                channel=args.get(
                    "channel",
                    "#general"
                ),

                message=args.get(
                    "message",
                    ""
                )

            )


        # ==================================================
        # CALENDAR
        # ==================================================

        elif tool == "CreateCalendarEn":

            result = create_calendar_event(

                title=args.get(
                    "title",
                    "Meeting"
                ),

                date=args.get(
                    "start",
                    ""
                )

            )


        # ==================================================
        # JIRA
        # ==================================================

        elif tool == "Jira_Tool":

            result = create_jira_ticket(

                summary=args.get(
                    "title",
                    "Task"
                ),

                description=args.get(
                    "description",
                    ""
                )

            )


        # ==================================================
        # RAG
        # ==================================================

        elif tool == "RAG_Tool":

            result = send_rag_query(

                query=args.get(
                    "query"
                )
                or args.get(
                    "task",
                    ""
                )

            )


        # ==================================================
        # UNKNOWN
        # ==================================================

        else:

            result = {

                "status": "failed",

                "error": (
                    f"Unknown tool: {tool}"
                )

            }


        results.append({

            "tool": tool,

            "result": result

        })


    return {

        "tool_results": results,

        "messages": [

            f"[Executor] Executed "
            f"{len(results)} approved action(s)"

        ],

        "status": "executed"

    }
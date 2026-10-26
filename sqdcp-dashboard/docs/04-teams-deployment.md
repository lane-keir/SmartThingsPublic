# 4. Hosting the dashboard in Microsoft Teams

There are three ways to host the dashboard, and you can combine them. **Option A is
the recommended baseline.** Option B adds the dashboard to the daily meeting itself.
Option C gives leaders a branded app on the Teams left rail.

## Before you start

| Item | Detail |
|---|---|
| Workspace | Create **Operations – SQDCP** in the Power BI service and publish the report into it |
| Licensing | Every viewer needs **Power BI Pro** (or PPU), **unless** the workspace is on **Premium / Fabric F64+**. Then free users can view |
| Access | Share through a **Power BI app** with an Entra ID (security) group, e.g. `SG-SQDCP-Viewers`. A Teams tab does **not** grant access to the report on its own |
| Refresh | Gateway and schedule set up as in [02-data-sources.md](02-data-sources.md) |

**Publish the Power BI app.** In the workspace choose **Create app**. Name it
*SQDCP Start of Shift*, include the report, set the audience to
`SG-SQDCP-Viewers`, and publish. Users then always see the curated app version,
and you can keep developing in the workspace.

## Option A: tab in the Operations team channel (recommended)

1. In Teams, open the **Operations** team (or create one) and add a channel called
   **Start of Shift**.
2. Click **+** (Add a tab), choose **Power BI**, then pick *SQDCP Start of Shift*
   from the app or workspace.
3. Next to it, add tabs for the **Tier1 Actions** and **Customer Visits** Microsoft
   Lists. Leads can then raise actions in the meeting, and they reach the dashboard
   at the next refresh.
4. Pin a channel post with how-to notes: the meeting standard, the KPI definitions
   (link [01-kpi-definitions.md](01-kpi-definitions.md)), and who owns the data.

## Option B: inside the recurring start-of-shift Teams meeting

1. Create the recurring meeting, for example 06:15 every weekday, 15 minutes.
   Better still, create it **in the Start of Shift channel** so the chat and files
   stay with the team.
2. In the meeting, click **+** (Apps), choose **Power BI** and pick the report. It
   then opens as a meeting tab for every attendee, before, during and after the meeting.
3. The facilitator shares the Power BI tab or window, so remote attendees see the
   same board as the room.
4. On the shopfloor, use a **Teams Rooms** device or a TV with a kiosk PC that joins
   the meeting. Or open the report in Power BI **full-screen mode** from a licensed
   service account.

> Never use *Publish to web* for this report. It makes the data public on the internet.

## Option C: custom "SQDCP Start of Shift" Teams app (left-rail icon)

The package in [`teams-app/`](../teams-app) is a Teams app with a personal tab that
opens the report through Power BI secure embed (`reportEmbed?…&autoAuth=true`).

1. Open the report in the Power BI service and copy the IDs from its URL:
   `https://app.powerbi.com/groups/<WORKSPACE_ID>/reports/<REPORT_ID>/<PAGE_NAME>?ctid=<TENANT_ID>`
2. Build the package:
   ```bash
   python3 tools/package_teams_app.py --tenant <TENANT_ID> --workspace <WORKSPACE_ID> \
       --report <REPORT_ID> --page <PAGE_NAME> --company "Your Company"
   ```
   This creates `teams-app/build/sqdcp-teams-app.zip`.
3. To test it, go to Teams **Apps > Manage your apps > Upload an app > Upload a
   custom app**. Custom app upload must be allowed for you.
4. To roll it out, send the zip to your **Teams admin**. They upload it in **Teams
   admin center > Teams apps > Manage apps > Upload new app**. Then, under **Setup
   policies**, they can **pin it to the app bar** for production leaders.
5. The app inherits the viewer's own Power BI permissions, so access is still
   controlled by the Power BI app audience.

Test step 3 before rolling out. The secure-embed sign-in inside Teams depends on
your tenant's conditional access settings. If users are asked to sign in
repeatedly, use Option A. Your admin can still pin the built-in **Power BI** Teams
app to the app bar with a setup policy, which gives the same left-rail access
without a custom package.

## Notifications & subscriptions

* **Morning email or Teams digest.** In the report choose **Subscribe > Create a
  subscription** for page 1 at 05:50, to the shift-lead group. Leaders arrive having
  already seen it.
* **Red alerts into Teams.** Set a data alert on the `Accidents` and `Escapes`
  dashboard tiles. A Power Automate flow then posts to the Start of Shift channel,
  as in step 7 of the build guide.
* **Chat in Teams.** On any visual, **Share > Chat in Teams** starts a conversation
  with a deep link back to the exact view. Use it for follow-ups after the meeting.

## Go-live checklist

- [ ] Every KPI has a named data owner and a live (or scheduled-drop) source
- [ ] Each KPI checked against its source system for at least 5 days
- [ ] Refresh runs about 45 min before each shift, and failure emails go to the owner
- [ ] `pUtcOffsetHours` matches the current clock offset (check at BST changeover)
- [ ] Power BI app published to the viewer group, and Teams tab added
- [ ] Meeting standard agreed: S → Q → D → C → P, reds and ambers only, 15 minutes, actions logged
- [ ] Targets reviewed by the Ops Manager in the KPI master

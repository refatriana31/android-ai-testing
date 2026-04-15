# UAT Catalog — bawana_revamp mobile

Total scenarios: **139** (cleaned from `Untitled spreadsheet - Sheet1.csv`).

Legend:
- ✅ **covered** — already implemented under `tests/`
- 🟢 **generated** — .md scaffolded this pass (High priority only)
- ⏭️ **skipped** — not realistic under current pipeline (reason given)
- ⏸️ **deferred** — Medium/Low priority, scaffold later on demand

| UAT ID | Section | Priority | Scenario | Status |
|---|---|---|---|---|
| AUTH-M-001 | 4.1 User Authentication | High | Learner logs in via mobile using valid credentials | ✅ `tests/03-login-valid.md` |
| AUTH-M-002 | 4.1 User Authentication | High | Invalid password shows clear error on mobile | ✅ `tests/04-login-invalid.md` |
| AUTH-M-004 | 4.1 User Authentication | High | First-time login with default password prompts password change | ⏭️ skipped (requires pre-provisioned new account) |
| AUTH-M-005 | 4.1 User Authentication | High | Learner requests forgot password from mobile login screen | ⏭️ skipped (requires email access) |
| AUTH-M-006 | 4.1 User Authentication | High | Learner resets password from email link on mobile | ⏭️ skipped (requires email access) |
| AUTH-M-007 | 4.1 User Authentication | High | Learner changes password from account settings on mobile | ✅ `tests/05-change-password.md` |
| AUTH-M-011 | 4.1 User Authentication | High | Learner logs out securely from mobile | 🟢 `tests/07-auth-m-011.md` |
| HOME-M-001 | 4.2 Homepage Sections | High | Homepage loads after mobile login | 🟢 `tests/08-home-m-001.md` |
| HOME-M-004 | 4.2 Homepage Sections | High | My Assignments section shows Given, In Progress, and Done states | 🟢 `tests/09-home-m-004.md` |
| HOME-M-005 | 4.2 Homepage Sections | High | Homepage shows ongoing or upcoming events relevant to learner | 🟢 `tests/10-home-m-005.md` |
| HOME-M-007 | 4.2 Homepage Sections | High | Interest-based recommendation block appears on mobile homepage | 🟢 `tests/11-home-m-007.md` |
| HOME-M-008 | 4.2 Homepage Sections | High | Recent Activity shows unfinished or in-progress learning items | 🟢 `tests/12-home-m-008.md` |
| LIB-M-001 | 4.3 Learning Library | High | Learner opens Library from mobile navigation | 🟢 `tests/13-lib-m-001.md` |
| LIB-M-002 | 4.3 Learning Library | High | Learner navigates the 5-level library hierarchy | 🟢 `tests/14-lib-m-002.md` |
| LIB-M-003 | 4.3 Learning Library | High | Search returns relevant learning content on mobile | 🟢 `tests/15-lib-m-003.md` |
| LIB-M-006 | 4.3 Learning Library | High | SCORM or interactive module content opens correctly on mobile and can be started | ⏭️ skipped (SCORM interactive module) |
| LIB-M-012 | 4.3 Learning Library | High | Learner can answer and submit an essay-type quiz question from mobile | 🟢 `tests/16-lib-m-012.md` |
| LIB-M-014 | 4.3 Learning Library | High | Learner can use Save and Exit during a quiz or test on mobile without losing answered responses | 🟢 `tests/17-lib-m-014.md` |
| LIB-M-015 | 4.3 Learning Library | High | Saved quiz or test attempt resumes from the latest saved state on mobile | 🟢 `tests/18-lib-m-015.md` |
| JRN-M-001 | 4.4 Learning Journey | High | Learner opens Learning Journey from mobile navigation | 🟢 `tests/19-jrn-m-001.md` |
| JRN-M-002 | 4.4 Learning Journey | High | Journey detail shows its component tracks | 🟢 `tests/20-jrn-m-002.md` |
| JRN-M-004 | 4.4 Learning Journey | High | Journey progress updates after learner completes a child activity | 🟢 `tests/21-jrn-m-004.md` |
| FLOW-M-001 | 4.5 Learning Flow | High | Pre-test appears before content when configured | 🟢 `tests/22-flow-m-001.md` |
| FLOW-M-002 | 4.5 Learning Flow | High | Content status moves through Not Started, Started, and Finished | 🟢 `tests/23-flow-m-002.md` |
| FLOW-M-003 | 4.5 Learning Flow | High | Learner can resume an unfinished course on mobile | 🟢 `tests/24-flow-m-003.md` |
| FLOW-M-004 | 4.5 Learning Flow | High | Prerequisite blocks next content or course until earlier requirement is complete | 🟢 `tests/25-flow-m-004.md` |
| FLOW-M-005 | 4.5 Learning Flow | High | Post-test appears after content when configured | 🟢 `tests/26-flow-m-005.md` |
| FLOW-M-006 | 4.5 Learning Flow | High | Passing score marks course complete | 🟢 `tests/27-flow-m-006.md` |
| FLOW-M-007 | 4.5 Learning Flow | High | Failing score does not mark course complete | 🟢 `tests/28-flow-m-007.md` |
| FLOW-M-008 | 4.5 Learning Flow | High | Certificate becomes downloadable only after completion requirements are met | ⏭️ skipped (offline/download mode) |
| FLOW-M-012 | 4.5 Learning Flow | High | Double tap or network interruption during submit does not create duplicate attempt | ⏭️ skipped (infra-level race/network) |
| ASG-M-001 | 4.6 Assignment | High | Assigned course, journey, or project appears in My Assignments on mobile | 🟢 `tests/29-asg-m-001.md` |
| ASG-M-002 | 4.6 Assignment | High | Assignment detail shows due date, points, and certificate information when configured | 🟢 `tests/30-asg-m-002.md` |
| ASG-M-003 | 4.6 Assignment | High | Assignment status updates from Given to In Progress to Done based on learner activity | 🟢 `tests/31-asg-m-003.md` |
| EVT-M-001 | 4.7 Events | High | Accessible events appear on the homepage mobile events block | 🟢 `tests/32-evt-m-001.md` |
| EVT-M-002 | 4.7 Events | High | Learner can register for a public event on mobile | 🟢 `tests/33-evt-m-002.md` |
| EVT-M-010 | 4.7 Events | High | Double tap on register does not create duplicate registration | ⏭️ skipped (infra-level race/network) |
| REC-M-001 | 4.9 Personalized Recommendations | High | Learner can open topic or interest selection on mobile | 🟢 `tests/34-rec-m-001.md` |
| REC-M-002 | 4.9 Personalized Recommendations | High | Learner can select and save interests on mobile | 🟢 `tests/35-rec-m-002.md` |
| REC-M-003 | 4.9 Personalized Recommendations | High | Homepage recommendations reflect the learner's selected interests | 🟢 `tests/36-rec-m-003.md` |
| ACT-M-001 | 4.10 User Activity View | High | Learner can open user activity view on mobile | 🟢 `tests/37-act-m-001.md` |
| ACT-M-002 | 4.10 User Activity View | High | User activity shows course progress per learning item | 🟢 `tests/38-act-m-002.md` |
| TEAM-M-001 | 4.11 Team Activity View | High | Manager can open Team Activity View from the mobile app | ⏭️ skipped (manager persona (different account needed)) |
| TEAM-M-002 | 4.11 Team Activity View | High | Manager can see team member list with progress breakdown | ⏭️ skipped (manager persona (different account needed)) |
| TEAM-M-005 | 4.11 Team Activity View | High | Non-manager user cannot access Team Activity View | ⏭️ skipped (manager persona (different account needed)) |
| PRO-M-001 | 4.13 User Profile | High | Learner can open profile on mobile | 🟢 `tests/39-pro-m-001.md` |
| PRO-M-003 | 4.13 User Profile | High | Learner can upload or change profile photo from mobile | ⏭️ skipped (requires camera/gallery) |
| CAL-M-001 | 4.14 Calendar | High | Learner can open calendar on mobile | 🟢 `tests/40-cal-m-001.md` |
| SEC-M-001 | 4.16 Account & Security | High | Learner changes password successfully from mobile account settings | ✅ `tests/05-change-password.md` |
| SEC-M-003 | 4.16 Account & Security | High | Forgot password email flow works end to end on mobile | ⏭️ skipped (requires email access) |
| SEC-M-004 | 4.16 Account & Security | High | Logout ends session securely on mobile | 🟢 `tests/41-sec-m-004.md` |
| CON-M-001 | 4.17 Content Player | High | Resume learning progress for audio, video, pdf & scorm  | ⏭️ skipped (SCORM interactive module) |
| CON-M-007 | 4.17 Content Player | High | Learner can download a PDF content file from mobile when download is allowed | ⏭️ skipped (offline/download mode) |
| CON-M-002 | 4.17 Content Player | High | Download content to play offline for video & audio.   | ⏭️ skipped (offline/download mode) |
| CON-M-003 | 4.17 Content Player | High | Download and play SCORM content | ⏭️ skipped (SCORM interactive module) |
| AUTH-M-003 | 4.1 User Authentication | Medium | Learner logs in using SSO on mobile when SSO is enabled | ⏸️ deferred |
| AUTH-M-008 | 4.1 User Authentication | Medium | Wrong current password blocks password change | ⏸️ deferred |
| AUTH-M-009 | 4.1 User Authentication | Medium | Show-hide password control works on mobile without covering input | ⏸️ deferred |
| AUTH-M-010 | 4.1 User Authentication | Medium | Mobile keyboard does not hide login CTA or validation message | ⏸️ deferred |
| AUTH-M-012 | 4.1 User Authentication | Medium | Expired session returns learner safely to login screen on reopen | ⏸️ deferred |
| HOME-M-002 | 4.2 Homepage Sections | Medium | Banner carousel is visible and swipeable on mobile | ⏸️ deferred |
| HOME-M-003 | 4.2 Homepage Sections | Medium | Tapping banner opens the correct target | ⏸️ deferred |
| HOME-M-006 | 4.2 Homepage Sections | Medium | Popular Channel section is visible when recommendation data exists | ✅ `tests/06-popular-channel.md` |
| HOME-M-009 | 4.2 Homepage Sections | Medium | Homepage handles missing data with clean empty states | ⏸️ deferred |
| HOME-M-010 | 4.2 Homepage Sections | Medium | Long titles on cards do not break mobile layout | ⏸️ deferred |
| HOME-M-011 | 4.2 Homepage Sections | Medium | Scrolling homepage with multiple sections remains responsive | ⏸️ deferred |
| HOME-M-012 | 4.2 Homepage Sections | Medium | Tapping a card from homepage opens the correct destination | ⏸️ deferred |
| LIB-M-004 | 4.3 Learning Library | Medium | No-result search shows a clear empty state | ⏸️ deferred |
| LIB-M-005 | 4.3 Learning Library | Medium | Video content opens and is playable on mobile | ⏸️ deferred |
| LIB-M-007 | 4.3 Learning Library | Medium | Audio content opens and is playable on mobile | ⏸️ deferred |
| LIB-M-008 | 4.3 Learning Library | Medium | Document content opens in a readable mobile viewer | ⏸️ deferred |
| LIB-M-009 | 4.3 Learning Library | Medium | Linked content opens safely from mobile | ⏸️ deferred |
| LIB-M-010 | 4.3 Learning Library | Medium | Quiz multiple choice embedded in course is accessible on mobile | ⏸️ deferred |
| LIB-M-011 | 4.3 Learning Library | Medium | Quiz question and answer options that contain images render clearly on mobile | ⏸️ deferred |
| LIB-M-013 | 4.3 Learning Library | Medium | Essay or project result shows a clear pending-grading state before manual grading is finished | ⏸️ deferred |
| LIB-M-016 | 4.3 Learning Library | Medium | Learner can review quiz result details with correct and incorrect indicators after submission when enabled | ⏸️ deferred |
| LIB-M-017 | 4.3 Learning Library | Medium | Project submission item is accessible from mobile library flow | ⏸️ deferred |
| LIB-M-018 | 4.3 Learning Library | Medium | Learner can narrow library content using tag or topic filters on mobile when tagging is enabled | ⏸️ deferred |
| LIB-M-019 | 4.3 Learning Library | Medium | Back navigation preserves prior list context in mobile library | ⏸️ deferred |
| JRN-M-005 | 4.4 Learning Journey | Medium | Learner can open a journey from assignment entry point | ⏸️ deferred |
| JRN-M-006 | 4.4 Learning Journey | Medium | Long journey titles and multiple items remain readable on small screens | ⏸️ deferred |
| FLOW-M-009 | 4.5 Learning Flow | Medium | Timer per test works correctly on mobile when enabled | ⏸️ deferred |
| FLOW-M-010 | 4.5 Learning Flow | Medium | Timer per question works correctly on mobile when enabled | ⏸️ deferred |
| FLOW-M-011 | 4.5 Learning Flow | Medium | Learner can submit project file from mobile | ⏸️ deferred |
| FLOW-M-013 | 4.5 Learning Flow | Medium | Learner can upload multiple files to a project submission from mobile when multiple upload is allowed | ⏸️ deferred |
| ASG-M-004 | 4.6 Assignment | Medium | Assignment notification deep-link opens the correct assignment on mobile | ⏸️ deferred |
| ASG-M-005 | 4.6 Assignment | Medium | Due soon or expired assignments are visually distinguishable on mobile | ⏸️ deferred |
| ASG-M-007 | 4.6 Assignment | Medium | Learner does not see assignment not targeted to them | ⏸️ deferred |
| EVT-M-003 | 4.7 Events | Medium | Invite-only or non-public event is visible only to invited learner | ⏸️ deferred |
| EVT-M-004 | 4.7 Events | Medium | Online event detail shows join method clearly on mobile | ⏸️ deferred |
| EVT-M-005 | 4.7 Events | Medium | Offline event detail shows time and location clearly on mobile | ⏸️ deferred |
| EVT-M-006 | 4.7 Events | Medium | Pre-test or post-test attached to event is accessible on mobile | ⏸️ deferred |
| EVT-M-007 | 4.7 Events | Medium | Survey attached to event is accessible on mobile | ⏸️ deferred |
| EVT-M-008 | 4.7 Events | Medium | Event appears in learner calendar on correct date | ⏸️ deferred |
| EVT-M-009 | 4.7 Events | Medium | Full or unavailable event blocks extra registration on mobile | ⏸️ deferred |
| EVT-M-012 | 4.7 Events | Medium | Learner can access QR or barcode attendance flow for an offline event on mobile when it is used | ⏸️ deferred |
| EVT-M-015 | 4.7 Events | Medium | Learner can select the intended batch or session for a multi-batch event on mobile | ⏸️ deferred |
| LDB-M-001 | 4.8 Leaderboard | Medium | Learner can open leaderboard on mobile | ⏸️ deferred |
| LDB-M-002 | 4.8 Leaderboard | Medium | Leaderboard shows learner rank and total points | ⏸️ deferred |
| LDB-M-003 | 4.8 Leaderboard | Medium | Leaderboard updates after learner completes a point-earning activity | ⏸️ deferred |
| LDB-M-005 | 4.8 Leaderboard | Medium | Learner can still find own rank on long leaderboard list in mobile | ⏸️ deferred |
| LDB-M-006 | 4.8 Leaderboard | Medium | Search returns relevant user | ⏸️ deferred |
| REC-M-004 | 4.9 Personalized Recommendations | Medium | Popular Channel updates according to interest context when applicable | ⏸️ deferred |
| ACT-M-003 | 4.10 User Activity View | Medium | User activity shows total learning duration | ⏸️ deferred |
| ACT-M-004 | 4.10 User Activity View | Medium | Latest access timestamps are visible and current | ⏸️ deferred |
| ACT-M-005 | 4.10 User Activity View | Medium | Progress in user activity matches progress shown inside course detail | ⏸️ deferred |
| TEAM-M-003 | 4.11 Team Activity View | Medium | Manager can see learning hours or activity duration per team member | ⏸️ deferred |
| TEAM-M-004 | 4.11 Team Activity View | Medium | Manager can drill down to a team member activity detail view | ⏸️ deferred |
| TEAM-M-006 | 4.11 Team Activity View | Medium | Manager with no direct reports sees a clean empty state | ⏸️ deferred |
| TEAM-M-007 | 4.11 Team Activity View | Medium | Long team member names do not break row layout on small screens | ⏸️ deferred |
| TEAM-M-008 | 4.11 Team Activity View | Medium | Large team list remains scrollable and usable on mobile | ⏸️ deferred |
| INT-M-001 | 4.12 Course Interactions | Medium | Learner can like a course from mobile | ⏸️ deferred |
| INT-M-003 | 4.12 Course Interactions | Medium | Learner can share a course via mobile share action | ⏸️ deferred |
| INT-M-004 | 4.12 Course Interactions | Medium | Learner can bookmark or star a course for later | ⏸️ deferred |
| INT-M-005 | 4.12 Course Interactions | Medium | Bookmarked course appears in Playlist on mobile | ⏸️ deferred |
| INT-M-007 | 4.12 Course Interactions | Medium | Learners can submit comments in the comment box, and other users can view the comments posted by the employee. | ⏸️ deferred |
| PRO-M-002 | 4.13 User Profile | Medium | Profile shows name, email, and photo when available | ⏸️ deferred |
| PRO-M-004 | 4.13 User Profile | Medium | Learner can edit allowed profile details on mobile | ⏸️ deferred |
| PRO-M-005 | 4.13 User Profile | Medium | Invalid photo type or failed upload is handled gracefully | ⏸️ deferred |
| PRO-M-006 | 4.13 User Profile | Medium | Updated profile information is reflected when profile is reopened | ⏸️ deferred |
| CAL-M-002 | 4.14 Calendar | Medium | Month view shows events and assignments on correct dates | ⏸️ deferred |
| CAL-M-003 | 4.14 Calendar | Medium | Learner can switch between day, week, month, and list views on mobile | ⏸️ deferred |
| CAL-M-004 | 4.14 Calendar | Medium | Events and assignments use clear color or visual distinction | ⏸️ deferred |
| CAL-M-005 | 4.14 Calendar | Medium | Overlapping tasks are visible clearly on mobile | ⏸️ deferred |
| CAL-M-006 | 4.14 Calendar | Medium | Tapping a calendar item opens the correct detail | ⏸️ deferred |
| CAL-M-007 | 4.14 Calendar | Medium | Date and due information in calendar matches item detail | ⏸️ deferred |
| FDB-M-001 | 4.15 Grading | Medium | Learner can view feedback and result on submitted project from mobile | ⏸️ deferred |
| SEC-M-002 | 4.16 Account & Security | Medium | Weak or invalid new password is rejected according to rules | ⏸️ deferred |
| SEC-M-005 | 4.16 Account & Security | Medium | Reopening the app after logout does not restore protected session accidentally | ⏸️ deferred |
| LIB-M-020 | 4.3 Learning Library | Low | Orientation change does not break the library list or detail page | ⏸️ deferred |
| JRN-M-003 | 4.4 Learning Journey | Low | Locked journey item shows why it cannot be opened yet | ⏸️ deferred |
| ASG-M-008 | 4.6 Assignment | Low | Long assignment titles do not break mobile list layout | ⏸️ deferred |
| LDB-M-004 | 4.8 Leaderboard | Low | Tie ordering remains consistent when users have equal points | ⏸️ deferred |
| REC-M-005 | 4.9 Personalized Recommendations | Low | No-interest state shows a safe fallback rather than broken recommendations | ⏸️ deferred |
| INT-M-002 | 4.12 Course Interactions | Low | Like state persists after closing and reopening the page | ⏸️ deferred |
| INT-M-006 | 4.12 Course Interactions | Low | Learner can remove a bookmarked course from Playlist | ⏸️ deferred |
| CAL-M-008 | 4.14 Calendar | Low | Calendar empty state is clear when learner has no upcoming items | ⏸️ deferred |
| FDB-M-002 | 4.15 Grading | Low | Feedback notification deep-link opens the correct result page on mobile | ⏸️ deferred |
| ASG-M-006 | 4.6 Assignment | ASG-M-006 | ASG-M-006 | ⏸️ deferred |

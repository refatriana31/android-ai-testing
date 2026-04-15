---
id: 06-popular-channel
title: Popular Channel section visible on homepage when recommendation data exists
priority: medium
timeout_seconds: 120
---

## Setup
- Reset app state: `adb shell pm clear com.example.bawana_revamp`
- Site name `$SITE_NAME` (default `permata-revamp-stg`)
- Login via `$TEST_USER` / `$TEST_PASS`
- Learner must have interests / recommendation data for Popular Channel to show.
  If the user has no interests set, this test may legitimately be skipped or
  recorded as "precondition not met" (expected behavior, not a failure of the
  section).

## Steps
1. Launch app after pm clear
2. Enter site name and tap Next
3. Login with credentials
4. Handle onboarding (language Confirm; skip assessment)
5. Ensure Home tab is active (tap Home on bottom nav if needed)
6. Scroll/inspect the Home feed; look for a section labeled "Popular Channel"
   (variations accepted: "Popular Channels", "Channel Populer")
7. If Popular Channel section is present:
   - Confirm it contains one or more tappable cards (items with clickable area)
   - Tap the first card and confirm navigation to a detail/content screen
     (UI tree changes, new screen loaded)
   - Press BACK to return

## Expected
- Positive case: section header "Popular Channel" visible in the Home UI tree,
  with ≥1 tappable item below it, and tapping a card opens a new screen.
- Negative case (precondition not met): section is absent — record status
  `passed` with note `"precondition: learner has no recommendation/interest
  data → Popular Channel correctly hidden"`.
- Failure: section visible but cards are not tappable (no navigation on tap) OR
  section title misspelled / present but empty / crashes on tap.

## Notes
- "Popular Courses" is a DIFFERENT section and should not be confused.
- Do not enroll in or start any course — this test is read-only verification.

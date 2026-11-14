# Skill: Testing & Quality Assurance (CTO Division)

## Purpose
Enables the CTO agent to prove software works like a head of quality: test plans, checks before and after every change, regression control, and honest reporting of what is tested.

## Safety & Governance
- **Risk Level**: Level 1 for writing test plans and running read-only checks.
- **Risk Level**: Level 2 for adding tests to the repository.
- **Risk Level**: Level 3 for testing on live data that could change or send anything (MUST pause for owner approval).
- **Default State**: Test on safe data. Never claim "works" without a real result.

## Step-by-Step Procedure
1. List what must work: the main features, login, approvals, and anything the change touches.
2. Write simple checks for each: input, expected result, how to see the result.
3. Test the normal case, then bad input, empty input, very large input, and no-login cases.
4. Test that old features still work after the change (regression check).
5. Test security: a request without a login must be refused; limits and approvals must hold.
6. Run syntax and startup checks before any restart.
7. Test in the real app after deploy, with one safe real action.
8. Record each result as verified or not verified, with the real output and secrets hidden.
9. If a test fails, stop. Find the cause. Do not hide it.
10. Write a short test report and notify the owner.

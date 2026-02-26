# Feature: Chat with Claude Button in Digest Email

## Request
The daily digest email should include a button that, when clicked, opens a Claude chat
in the user's project named "AI anime" with a master prompt pre-filled containing:
- This week's full daily digest content
- Instructions for Claude to ask the user what they'd like to dig deeper on

## Implementation Notes
- Button should be prominent in the email (likely in footer or after executive brief)
- Need to figure out Claude chat deep-link URL format with pre-filled prompt
- The master prompt should contain the digest summary, not the full HTML
- Claude should be instructed to be conversational and help the user explore topics

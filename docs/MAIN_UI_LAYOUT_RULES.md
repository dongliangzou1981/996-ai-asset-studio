# Main UI Layout Rules

## Scope

These rules define the minimum operation-safe layout for 996 legend game `main_ui` generation.

The style can change. The basic operation logic must not be broken.

## Required Player Info Area

The main UI must keep a readable player information area with:

- avatar
- name
- level
- health bar
- mana bar

This area must not be hidden, cropped, or covered by decorative elements.

## Required Main Function Entries

The main UI must keep visible entries for:

- bag
- role
- skills
- shop
- activity
- settings

These entries may use different icon styles, colors, borders, and ornaments, but they must remain recognizable as clickable UI controls.

## Required Bottom Operation Area

The bottom operation area must keep:

- skill bar
- shortcut bar

The generated image should keep enough visual separation between slots and buttons for later component slicing and candidate detection.

## Required Chat Area

The chat area must stay visible and unobstructed.

It may move within a reasonable main UI layout, but it must not overlap the skill bar, shortcut bar, or player information area.

## Required Map Entry

The main UI must keep a map or minimap entry.

The entry can vary in frame style, border ornament, and color, but it must remain visually distinct.

## Required Right-Side Function Menu

The right-side function menu must remain available for secondary actions and event entries.

It may collapse into a compact icon stack, but the core actions should not disappear.

## Allowed Variation

The generator may vary:

- colors
- ornaments
- borders
- buttons
- icons
- fonts
- textures

These variations define the style code identity.

## Forbidden Changes

The generator must not:

- delete core entries
- hide core entries
- break the operation flow
- make buttons look non-clickable
- cover the chat area
- cover the skill bar
- cover the shortcut bar
- cover player information

## Production Notes

The `main_ui` generated in Master Style Workflow is the source of the style code.

Future screens such as `role_ui`, `bag_ui`, `shop_ui`, and `activity_ui` should inherit:

- color palette
- font style
- border style
- button style
- icon style
- texture style

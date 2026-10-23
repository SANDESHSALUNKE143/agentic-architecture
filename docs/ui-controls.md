# Console controls

Every text box, checkbox, radio, and dropdown in the console comes from the `@agentic/controls` package at `packages/controls`. A screen does not write its own `<input>`, `<textarea>`, or `<select>`.

The package draws the dropdown menu. The browser's gray menu is not used. A checkbox keeps its label beside the box. Text, password, number, and long text share one field layout.

## Use a control

Import the control in the screen:

```tsx
import { Checkbox, Select, TextField } from "@agentic/controls";
```

| Control | When |
| --- | --- |
| TextField | A URL, a connection string, a username, a password, or a search box |
| TextArea | A prompt, a note, or the chat brief |
| NumberField | An approval amount |
| Checkbox | A yes or no choice |
| RadioGroup | A short set of choices, such as the model |
| Select | A list such as the vector store, the embedding, or how often ingestion runs |
| GearButton | Opens that agent's configuration. The Configuration navigation item uses the same gear |

The agent picker is a search list built for choosing one agent. Its search box is still a `TextField`.

## Check

`npm test` in `apps/admin-dashboard` opens the dropdown, toggles a checkbox, types in a text field, and fails if a screen adds a native form tag.

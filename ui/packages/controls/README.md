# @agentic/controls

The console's form controls. Screens import these instead of writing a raw text box, checkbox, radio, or dropdown.

| Control | Use |
| --- | --- |
| `TextField` | One line of text, including a password or a search box |
| `TextArea` | A prompt, a note, or the chat brief |
| `NumberField` | An amount |
| `Checkbox` | A yes or no choice, with the label beside the box |
| `RadioGroup` | One choice from a short row, such as the model |
| `Select` | A longer list. The menu is drawn by this package |
| `GearButton` | Opens one agent's settings. The same gear is used on every screen |

`Select` does not render a native menu. The open list uses the same mark, type, and surface as the agent picker.

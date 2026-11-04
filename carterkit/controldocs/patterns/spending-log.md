---
kind: pattern
id: spending-log
family: trackers-and-logs
title: Spending log: add, review, trend
intents: ["log expenses", "budget tracker", "track spending", "enter a transaction", "expense history"]
parts: [{"type": "textInput", "role": "amount and note"}, {"type": "picker", "role": "category"}, {"type": "button", "role": "save entry"}, {"type": "list", "role": "recent entries table"}, {"type": "chart", "role": "trend"}]
surfaces: ["app"]
theme: paper-and-ink
rules: ["Entry and review are different jobs: put Add and History on separate tabs.", "A list with listColumns reads as a table; give it the tab’s remaining height.", "Use a two-column grid on phones when the tab is mostly inputs."]
exampleRef: intermediate/budget-tracker
---

Anything you both write to and read back wants an input tab and a history tab. The input tab stays short so the keyboard never covers a button.

## Parts

- **textInput** (amount and note)
- **picker** (category)
- **button** (save entry)
- **list** (recent entries table)
- **chart** (trend)

## Rules

- Entry and review are different jobs: put Add and History on separate tabs.
- A list with listColumns reads as a table; give it the tab’s remaining height.
- Use a two-column grid on phones when the tab is mostly inputs.

## Example

Derived from `layout-library/intermediate/budget-tracker`. Decodes as a full layout.

```json
{
  "name": "Budget Tracker",
  "id": "spending-log",
  "version": 1,
  "headerTitle": "Budget",
  "accentColor": "#34D399",
  "theme": {
    "accentColor": "#34D399",
    "accentGradient": [
      "#34D399",
      "#059669"
    ],
    "cornerRadius": 14,
    "tabBarTint": "#34D399",
    "surfacePrimary": "#34D39914",
    "surfaceSecondary": "#34D3990A",
    "borderColor": "#34D3992E",
    "fontDesign": "rounded"
  },
  "tabs": [
    {
      "title": "History",
      "icon": "list.bullet.rectangle",
      "grid": {
        "columns": 2,
        "rows": 9
      },
      "children": [
        {
          "type": "chart",
          "id": "bt-monthly-chart",
          "position": [
            0,
            0
          ],
          "span": [
            4,
            2
          ],
          "label": "Spent vs budget",
          "formatValue": "currency",
          "chartConfig": {
            "showLegend": true,
            "barCornerRadius": 5,
            "yMin": 0,
            "scrub": true
          },
          "defaultValue": "{\"categories\": [\"Apr\", \"May\", \"Jun\", \"Jul\", \"Aug\", \"Sep\"], \"series\": [{\"name\": \"Spent\", \"type\": \"bar\", \"color\": \"#34D399\", \"values\": [2890, 3105, 2760, 3340, 2985, 2184]}, {\"name\": \"Budget\", \"type\": \"line\", \"color\": \"#F59E0B\", \"values\": [3200, 3200, 3200, 3200, 3200, 3200]}]}",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "budget_tracker_monthly"
              },
              "valuePath": "chart"
            }
          ]
        },
        {
          "type": "list",
          "id": "bt-transactions",
          "position": [
            4,
            0
          ],
          "span": [
            5,
            2
          ],
          "label": "Recent transactions",
          "listColumns": [
            {
              "key": "date",
              "label": "Date"
            },
            {
              "key": "merchant",
              "label": "Merchant"
            },
            {
              "key": "category",
              "label": "Category"
            },
            {
              "key": "amount",
              "label": "$",
              "format": "decimal:2"
            }
          ],
          "defaultValue": "[{\"date\": \"Sep 24\", \"merchant\": \"Trader Joe's\", \"category\": \"Groceries\", \"amount\": 64.18}, {\"date\": \"Sep 23\", \"merchant\": \"Shell\", \"category\": \"Transport\", \"amount\": 41.02}, {\"date\": \"Sep 23\", \"merchant\": \"Blue Bottle\", \"category\": \"Dining\", \"amount\": 6.75}, {\"date\": \"Sep 22\", \"merchant\": \"Comcast\", \"category\": \"Utilities\", \"amount\": 79.99}, {\"date\": \"Sep 21\", \"merchant\": \"AMC Metreon\", \"category\": \"Fun\", \"amount\": 31.5}, {\"date\": \"Sep 21\", \"merchant\": \"Chipotle\", \"category\": \"Dining\", \"amount\": 13.45}, {\"date\": \"Sep 20\", \"merchant\": \"Safeway\", \"category\": \"Groceries\", \"amount\": 88.62}, {\"date\": \"Sep 19\", \"merchant\": \"Clipper Card\", \"category\": \"Transport\", \"amount\": 25.0}, {\"date\": \"Sep 18\", \"merchant\": \"Walgreens\", \"category\": \"Other\", \"amount\": 17.34}]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "budget_tracker_transactions"
              },
              "valuePath": "rows"
            }
          ]
        }
      ]
    },
    {
      "title": "Add",
      "icon": "plus.circle.fill",
      "grid": {
        "columns": 2,
        "rows": 9
      },
      "children": [
        {
          "type": "group",
          "id": "bt-new-expense",
          "label": "New expense",
          "position": [
            0,
            0
          ],
          "span": [
            6,
            2
          ],
          "grid": {
            "columns": 2,
            "rows": 4
          },
          "children": [
            {
              "type": "textInput",
              "id": "bt-merchant",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Merchant",
              "placeholder": "e.g. Trader Joe's",
              "icon": "storefront",
              "autocorrect": true,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "budget_tracker_draft",
                  "field": "merchant",
                  "value": "{{value}}"
                }
              }
            },
            {
              "type": "stepper",
              "id": "bt-amount",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Amount ($)",
              "icon": "dollarsign.circle",
              "min": 0,
              "max": 2000,
              "step": 0.5,
              "defaultValue": 12.5,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "budget_tracker_draft",
                  "field": "amount",
                  "value": "{{value}}"
                }
              }
            },
            {
              "type": "picker",
              "id": "bt-category",
              "position": [
                2,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Category",
              "icon": "tag",
              "options": [
                "groceries",
                "dining",
                "transport",
                "utilities",
                "rent",
                "fun",
                "other"
              ],
              "optionLabels": [
                "Groceries",
                "Dining",
                "Transport",
                "Utilities",
                "Rent",
                "Fun",
                "Other"
              ],
              "optionIcons": [
                "cart",
                "fork.knife",
                "car",
                "bolt",
                "house",
                "gamecontroller",
                "ellipsis.circle"
              ],
              "defaultValue": "groceries",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "budget_tracker_draft",
                  "field": "category",
                  "value": "{{value}}"
                }
              }
            },
            {
              "type": "datePicker",
              "id": "bt-date",
              "position": [
                3,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Date",
              "datePickerMode": "date",
              "datePickerStyle": "compact",
              "defaultValue": "2026-09-24T12:00:00Z",
              "dateMin": "2026-01-01T00:00:00Z",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "budget_tracker_draft",
                  "field": "date",
                  "value": "{{value}}"
                }
              }
            }
          ]
        },
        {
          "type": "segmentedControl",
          "id": "bt-payment",
          "position": [
            6,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Paid with",
          "options": [
            "debit",
            "credit",
            "cash"
          ],
          "optionLabels": [
            "Debit",
            "Credit",
            "Cash"
          ],
          "defaultValue": "debit",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "budget_tracker_draft",
              "field": "payment",
              "value": "{{value}}"
            }
          }
        },
        {
          "type": "button",
          "id": "bt-save",
          "position": [
            7,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Log expense",
          "icon": "checkmark.circle.fill",
          "style": "filled",
          "tint": "#34D399",
          "haptic": "success",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "budget_tracker_commit",
              "source": "add_tab"
            }
          }
        },
        {
          "type": "label",
          "id": "bt-last-saved",
          "position": [
            8,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Last logged",
          "icon": "clock.arrow.circlepath",
          "defaultValue": "Trader Joe's · $64.18",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "budget_tracker_commit_ack"
              },
              "valuePath": "summary"
            }
          ]
        }
      ]
    }
  ]
}
```

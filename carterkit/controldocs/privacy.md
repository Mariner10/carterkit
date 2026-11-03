---
type: legal
label: Privacy Policy
icon: hand.raised.fill
category: legal
---

# CAR-TER Privacy Policy

**Effective date:** October 28, 2026

CAR-TER ("the app") is a JSON-driven remote-control app for iOS. This policy explains what data the app and its optional cloud service handle. The short version: **the app collects nothing that identifies you.** Your layouts and control traffic go only to a server you run (or, with the optional paid Connect+ feature, through our relay, described below). The one thing the app sends us on its own is **anonymous usage counts** — how many times the app was opened, which kinds of controls get used, whether a layout used a local server or Connect+ — with no identifiers, content, or location, and you can switch it off (see "Anonymous usage statistics"). If you connect an AI app, a copy of how your layouts are built goes to our cloud service so that AI can work on them (see "AI connector").

## Default use (no account, self-hosted)

When you use CAR-TER with your own MeshSocket server:

- The app connects **only to the server address you enter**. Your commands, telemetry, and chat messages travel between your device and your server. They are never sent to the developer.
- Layouts, chat history, and app preferences (such as your last-opened layout and first-run state) are stored **locally on your device**. We cannot see them.
- The app does **not** collect personal information, does **not** track you, and does **not** include advertising identifiers. The only analytics are the anonymous counts described below, which you can turn off.
- The optional **camera control** runs entirely on your device and only when you tap to start it. Scanned codes, recognized text, and snapshots travel **only to the server you configured** — never to the developer — and the app does not store them.

## Anonymous usage statistics

**Why I ask for this.** CAR-TER is built by one person, and it can be a remote for almost anything, so I honestly cannot tell what people build with it. Aggregate counts are how I find out which controls get real use, whether people run their own server or Connect+, where layouts get heavy, and where the app hangs — which is what decides what gets built next and fixed first. I am also a data-visualization person, and watching these numbers on a CAR-TER dashboard of my own is part of the fun. The deal is numbers only: I never want to know who you are, what your layouts are called, or what is on your screen, and the app shows you exactly what it last sent.

The app sends us **aggregate, de-identified usage counts** — numbers only:

- how many times the app was opened and roughly how long sessions last;
- how many layouts were loaded, how many tabs they had, and **which kinds of controls** they contain and get tapped (for example "12 button taps, 3 gauges shown") — never a control's name, label, value, or your layout's name;
- whether a layout talked to your own server, to Connect+, or to an HTTP/MQTT source, and how long the connection lasted — never the address, channel, or room;
- a verified founder flag, only for founder accounts, so the developer’s own activity can be filtered out;
- the Connect+ plan name, the app version, the iOS major version, and the device family (iPhone / iPad);
- the *category* of an error (for example "gateway"), never its text;
- which **named features** were used, as a count with no content: for example `template_install`, `layout_import`, `studio_push`, `hub_push` (a hub such as carterkit pushed a layout; tagged only with the connection kind `ws` or `connectplus`), `ai_applied` and `ai_undone` (an AI change was applied or undone), `add_hub_credential` (a Hub credential was created) and `import_link` (a template link was opened);
- once a day, iOS's own performance summary for the app — average launch time, time spent hung, peak memory, CPU and network volume — as numbers only, never crash logs or stack traces (separate switch: "Performance summaries").

The app does **not** send a user ID, device ID, advertising ID, push token, account, purchase, IP-derived location, or any content in usage payloads. Founder batches additionally send a Connect+ session credential in an authorization header solely to verify the founder flag. The servers do not retain that credential or its account with telemetry; only a verified true flag is stored. Other batches omit the flag and authorization header. To stop forged statistics, batches are signed with Apple's App Attest using a key the app creates fresh every day and discards with that day's token; our server checks the signature in the moment and keeps neither the key nor its identifier. Each day the app makes up a random token so we can count how many devices were active that day; it is discarded at midnight and cannot be joined across days. Our server keeps a hashed IP address for at most one hour purely to limit abuse, and does not store it with the counts.

**You can turn this off at any time** in Settings → Privacy & Data, which also shows you the exact contents of the last batch the app sent. When it is off the app records and sends nothing.

## Connect+ (optional paid cloud relay)

If you purchase **Connect+** and connect through our hosted relay (`connect.carterbeaudoin.net`) to receive push notifications, our relay stores the minimum needed to deliver those notifications:

- An **anonymous account identifier** that scopes your data and is not linked to your name or email.
- Your device's **Apple Push Notification token**, so alerts can be delivered to your device.
- The **alert rules** you configure (the conditions that trigger a notification).

We do **not** store your name, email address, contacts, or location. We do **not** sell or share this data, and we do **not** use it for advertising. Connect+ account identifiers and credentials are not stored with usage counts. The only derived account attribute stored with those counts is the verified founder flag described above.

## AI connector (optional)

Nothing below happens until you connect an AI app (for example Claude or ChatGPT) on the AI page in Settings and approve it on your phone.

- **What is copied to CAR-TER cloud** (`ai.carterbeaudoin.net`, hosted on Amazon Web Services): how your layouts are built (tabs, controls, labels, colours, the sources they read), the fields of your stores but **never the entries you typed**, which phone readings and widgets exist, the asks and hand-offs you send to your AI, the changes your AI proposes, and wireframe pictures of them (kept 7 days). Passwords and keys stay on your phone: layouts carry only placeholder names for them.
- **Who can read it**: only the AI apps you approved on this phone, each with its own sign-in that you can revoke. Changes an AI proposes reach your phone as suggestions; anything that adds a new outgoing connection waits for you to allow it.
- **Service log**: for reliability we log each AI request's tool name, timing and outcome against a salted hash of your space, never its content; these rows expire after 90 days.
- **Turning it off**: disconnect an AI on the AI page in Settings, or tap **Delete my cloud copy** there to remove the whole copy and disconnect every AI. Your layouts and entries stay on your phone.

## Rooms (live sharing)

When you share a layout as a Room or join one, the layout and its control changes, plus the display name you choose for the Room, travel through our relay to everyone in that Room. If the invite includes a room key, that traffic is end-to-end encrypted and the relay cannot read it; without one it is not. Leave the Room to stop.

## Payments and push notifications

- **Purchases** are handled entirely by **Apple** through the App Store. The app never receives or stores your payment details. We validate Apple's purchase receipt only to confirm your Connect+ entitlement.
- **Push notifications** are delivered through **Apple's Push Notification service (APNs)**, acting as a processor on our behalf. The app keeps up to 200 recent notifications locally on your device for Layout Info → Notifications. Opening a layout marks its notifications read; you can delete individual notifications or that layout's history there. Notification text is never sent with usage counts.

## Data retention and deletion

- Local data is removed when you delete the app from your device.
- Your AI connector copy stays until you delete it (Delete my cloud copy on the AI page in Settings); deleting it disconnects every AI. Wireframe links expire after 7 days and the service log after 90 days.
- Connect+ data (account identifier, push token, alert rules) is retained while your subscription is active and removed within a reasonable period after you cancel and stop using the relay. To request deletion, contact us at the address below.

## Children

CAR-TER is not directed to children and does not knowingly collect data from children.

## Changes

We may update this policy; the effective date above reflects the latest version. Material changes will be reflected on this page and in the app's bundled copy.

## Contact

Questions or data requests: support@carterbeaudoin.net

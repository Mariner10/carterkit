---
type: legal
label: Privacy Policy
icon: hand.raised.fill
category: legal
---

# CAR-TER Privacy Policy

**Effective date:** June 20, 2026

CAR-TER ("the app") is a JSON-driven remote-control app for iOS. This policy explains what data the app and its optional cloud service handle. The short version: **the app collects nothing that identifies you.** Your layouts and control traffic go only to a server you run (or, with the optional paid Connect+ feature, through our relay, described below). The one thing the app sends us on its own is **anonymous usage counts** — how many times the app was opened, which kinds of controls get used, whether a layout used a local server or Connect+ — with no identifiers, content, or location, and you can switch it off (see "Anonymous usage statistics").

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
- the Connect+ plan name, the app version, the iOS major version, and the device family (iPhone / iPad);
- the *category* of an error (for example "gateway"), never its text;
- once a day, iOS's own performance summary for the app — average launch time, time spent hung, peak memory, CPU and network volume — as numbers only, never crash logs or stack traces (separate switch: "Performance summaries").

The app does **not** send a user ID, device ID, advertising ID, push token, account, purchase, IP-derived location, or any content. Each day the app makes up a random token so we can count how many devices were active that day; it is discarded at midnight and cannot be joined across days. Our server keeps a hashed IP address for at most one hour purely to limit abuse, and does not store it with the counts.

**You can turn this off at any time** in Settings → Privacy & Data, which also shows you the exact contents of the last batch the app sent. When it is off the app records and sends nothing.

## Connect+ (optional paid cloud relay)

If you purchase **Connect+** and connect through our hosted relay (`connect.carterbeaudoin.net`) to receive push notifications, our relay stores the minimum needed to deliver those notifications:

- An **anonymous account identifier** that scopes your data and is not linked to your name or email.
- Your device's **Apple Push Notification token**, so alerts can be delivered to your device.
- The **alert rules** you configure (the conditions that trigger a notification).

We do **not** store your name, email address, contacts, or location. We do **not** sell or share this data, and we do **not** use it for advertising. Connect+ data is never combined with the anonymous usage counts above.

## Payments and push notifications

- **Purchases** are handled entirely by **Apple** through the App Store. The app never receives or stores your payment details. We validate Apple's purchase receipt only to confirm your Connect+ entitlement.
- **Push notifications** are delivered through **Apple's Push Notification service (APNs)**, acting as a processor on our behalf.

## Data retention and deletion

- Local data is removed when you delete the app from your device.
- Connect+ data (account identifier, push token, alert rules) is retained while your subscription is active and removed within a reasonable period after you cancel and stop using the relay. To request deletion, contact us at the address below.

## Children

CAR-TER is not directed to children and does not knowingly collect data from children.

## Changes

We may update this policy; the effective date above reflects the latest version. Material changes will be reflected on this page and in the app's bundled copy.

## Contact

Questions or data requests: support@carterbeaudoin.net

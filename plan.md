# Tailoring Business Agent — Project Plan

AI-Powered Order, Inventory, Production, Marketing, and Customer Planning System

---

## 01. Project Overview

**Project Name:** Tailoring Business Agent
**Project Type:** AI Agent / Business Operations System
**Domain:** Fashion Design, Custom Clothing, Small Business Operations
**Primary User:** the business owner

**Core Problem**
Managing a small custom clothing business involves keeping track of customer orders, deadlines, fabrics and other materials, production time, sourcing trips, alterations, college commitments, marketing/social media, and customer communication. These pieces of information are interconnected, but are often managed separately.

The Tailoring Business Agent is designed to bring these systems together. It acts as an intelligent production, business, and marketing assistant that understands:

- What orders exist
- Which orders are urgent
- What materials are available
- Which materials are reserved
- What needs to be sourced
- What projects are currently being worked on
- How much time each project requires
- When college commitments make production unavailable
- What needs to happen next
- What materials could be used for future designs
- What previous projects can inform new recommendations
- What current production activity could inform marketing/social content

The agent then uses this information to plan and continuously update the business workflow.

---

## 02. Core Concept

Turn the information surrounding the business into one interconnected system that can **reason** about orders, materials, time, and marketing, rather than treating each as a separate database.

The system should answer questions such as:

- What should I work on today?
- Which order should I prioritise?
- Do I have enough fabric for this order?
- Which materials need to be purchased?
- Can I combine these purchases into one sourcing trip?
- When can I realistically complete this order around college?
- What happens to my schedule if I don't finish today's work?
- What do I currently have in my inventory?
- What can I make from the fabric I currently own?
- What have I made in the past using similar materials?
- Can you make a catalogue of possible garments I can offer this customer?
- What should I post on Instagram this week based on what I'm currently making?

The differentiator is not any single feature — it's that orders, materials, time, history, and marketing all sit in one connected model, so a question about "today's priorities" can pull from all of these at once instead of requiring the business owner to check several separate tools and reconcile them manually.

---

## 03. Why This Needs an Agent

A conventional database can store: orders, materials, dates, projects.
A conventional calendar can store: classes, appointments, sewing sessions.
A conventional inventory system can store: fabric quantities, trims, notions, supplies.
A conventional social media scheduler can store: posts, captions, dates.

None of these systems inherently understands the relationships between them.

**The agent acts as the reasoning layer connecting them.**

For example: Order #24 requires 2.5 m of black denim and is due in five days. The system needs to determine:

1. Is black denim available?
2. How much is currently available?
3. Is some of it already reserved?
4. Does the order need sourcing?
5. How many hours will production take?
6. When is the next available sewing block?
7. Does that block conflict with college?
8. Are there other urgent orders?
9. When should cutting happen?
10. When should construction happen?
11. Does the resulting schedule meet the deadline?
12. Is there a stage of this project (e.g. the finished reveal) worth sharing on Instagram, and does the customer need to approve that first?

This is an agentic decision-making problem, rather than simply a data-storage problem.

---

## 04. Main Order Types

Every order belongs to one of three primary categories.

### 4.1 Date-Restricted Orders

These have a fixed deadline.

Examples: birthday outfits, event outfits, college events, fashion shows, competitions, weddings, gifts, specific customer delivery dates.

These orders have high priority because their deadline cannot easily move.

**Important information:** customer, garment, occasion, deadline, estimated production time, materials required, materials available, materials needing sourcing, current production stage, pickup/delivery requirement.

### 4.2 Exploratory Orders

Exploratory orders are less time-sensitive. The customer may know approximately what they want but may still be exploring garment type, silhouette, fabric, colour, construction, or overall design.

Exploratory orders are divided into two categories:

**Exploratory — Fabric Available**
The required fabric is already in inventory. Example: customer wants a blue cotton dress. The agent checks current blue cotton quantity, whether it is already reserved, previous projects using that fabric, typical material consumption, possible silhouettes, and whether enough fabric remains. The agent can then suggest feasible options.

**Exploratory — Fabric Needs Sourcing**
The design requires material that is not currently available. Example: customer wants a red satin dress; red satin: 0 m available. Rather than immediately treating this as a production task, the order becomes dependent on sourcing. The required material enters the sourcing system.

### 4.3 Alteration Orders

Alterations are treated separately because they generally have a different workflow and time requirement.

Examples: hemming, taking in, letting out, sleeve alterations, waist adjustments, repairs, zip replacement, restructuring, resizing.

Alterations may be strategically scheduled into smaller available time blocks between larger projects — e.g. a 30-minute alteration can be scheduled during a free block that would be unsuitable for a three-hour garment construction session.

---

## 05. Order Data Model

Each order should contain structured information.

**Basic information:** Order ID, Customer, Order type, Garment, Description, Date created, Status

**Time information:** Deadline, Estimated hours, Estimated number of sessions, Pickup/delivery date, Flexibility

**Material information:** Materials required, Quantity required, Materials available, Materials needing sourcing, Materials reserved

**Production information:** Design, Pattern, Cutting, Construction, Finishing, Alterations, Quality check, Completed

**Media:** Customer references, Sketches, Fabric photographs, Inspiration images, Progress photographs, Finished garment photographs

**Marketing (new):** Shareable flag (can this order's photos be posted publicly?), customer approval-to-post status, suggested post stage(s), linked draft posts

---

## 06. Priority System

The agent should calculate priority rather than relying entirely on manually assigned labels.

Priority can consider:

- **Deadline** — how soon is the order due?
- **Order type** — date-restricted orders generally take precedence over flexible exploratory orders.
- **Production time** — an order requiring eight hours needs to be planned earlier than one requiring one hour.
- **Material availability** — if materials are available, production can begin; if materials need sourcing, the agent must account for the sourcing dependency.
- **Sourcing time** — if a fabric requires a shopping trip, this becomes part of the production timeline.
- **Customer requirements** — certain customers or occasions may have specific constraints.
- **Current progress** — an almost-completed order may take priority over starting a new one.

### Priority Is Not Static

Priority should be recalculated when circumstances change.

Example: Monday — Order A is due in 10 days, Order B is due in 5 days. Order B is higher priority. But if Order B is waiting for fabric and Order A has all materials available, the agent may schedule work on Order A while adding sourcing for Order B. If the fabric for Order B is purchased on Tuesday, its priority and schedule can change again.

The agent should therefore treat priority as **dynamic**, recalculated on every relevant change, rather than a number permanently assigned to an order.

---

## 07. Materials Inventory

The inventory system should include all materials used across the business, not just fabric.

**Fabric:** cotton, denim, satin, linen, silk, net, jersey, knits, other textiles
**Trims:** lace, ribbons, bias tape, piping, elastic, decorative trims
**Fastenings:** zips, buttons, hooks and eyes, snaps, buckles
**Construction materials:** thread, interfacing, boning, fusible materials, needles
**Embellishment:** beads, sequins, embroidery materials, appliqué materials
**Packaging:** garment bags, boxes, tags, wrapping materials

### Fractional Inventory

A major requirement is that inventory should support fractional quantities. Fabric should not simply be available/unavailable — instead: black cotton: 4.75 m. Other examples: 1.35 m, 2.75 m, 0.65 m, 0.25 spool, 17 buttons, 3 zips. Different materials have different units.

| Material | Quantity | Unit |
|---|---|---|
| Black cotton | 4.75 | m |
| Blue denim | 3.20 | m |
| Gold lace | 7.50 | m |
| Thread | 0.40 | spool |
| Buttons | 18 | pieces |
| Zips | 6 | pieces |

### Physical, Reserved and Available Quantity

The inventory system should distinguish between three quantities:

- **Physical quantity** — the amount believed to physically exist.
- **Reserved quantity** — the amount allocated to existing projects.
- **Available quantity** — the amount that can still be allocated to another project.

Example — Black cotton: Physical 4.75 m, Reserved 2.50 m, Available 2.25 m.

The agent should use **available quantity** when deciding whether a new order can be accepted.

### Automatic Inventory Updates

Inventory should update based on project activity. When a project is created (e.g. 2.5 m black cotton required), the agent reserves 2.5 m. When the project is completed, the system records actual consumption (planned 2.50 m, actual 2.37 m) and inventory is updated using the actual amount — this prevents the system from permanently deducting estimated quantities when the actual amount used was different.

### Inventory History

Every material should maintain a transaction history, creating an audit trail:

```
BLACK COTTON
Initial inventory: 5.00 m
+2.00 m — Purchased
-1.65 m — Order #024
+3.00 m — Purchased
-2.20 m — Order #031
-0.35 m — Sample
Current physical quantity: 5.80 m
```

If an inventory number appears incorrect, the user can see how it was calculated.

### Manual Inventory Corrections

The user must always be able to correct the system — e.g. "I found another 0.5 m of the blue fabric" → the system records `+0.50 m — Manual inventory adjustment`. This matters because a physical inventory will never be perfectly represented by software.

### Project-Based Material Allocation

Each project should have a material requirement list, e.g.:

| Order #024 — Black Corset | Planned | Actual |
|---|---|---|
| Black denim | 1.80 m | 1.65 m |
| Lining | 1.20 m | 1.10 m |
| Boning | 6 pcs | 6 pcs |
| Zip | 1 pc | 1 pc |
| Thread | 0.20 spool | 0.15 spool |

This creates a relationship: **Order → Project → Materials → Inventory**

---

## 08. Material Sourcing

When materials are unavailable or insufficient, the agent creates sourcing requirements.

Example: Order #031 requires 3.2 m red satin; inventory has 1.4 m available. The agent calculates 1.8 m additional required. This requirement enters the sourcing system.

### Grouped Shopping Trips

The agent should avoid planning separate trips for every order — it groups material requirements. Example: three orders each need different fabrics; the agent identifies they can be sourced on the same trip and creates a single **Fabric Sourcing Trip** with a combined shopping list and the orders it's for.

### Shopping List Intelligence

The shopping list should not simply contain fabric names — it should include: material, required quantity, unit, orders requiring it, priority, colour, type, preferred characteristics, and additional supplies. Example: "Black denim — 3 m minimum, for Orders #24 and #31, medium/heavy weight preferred."

---

## 09. College Schedule Integration & Production Scheduling

The agent should understand that production happens around another schedule — the college calendar becomes one of the system's core constraints. The agent should account for: classes, exams, assignments, presentations, college events, holidays, existing appointments, free days, and preferred working hours.

The agent uses the intersection of **orders + deadlines + materials + production time + college schedule** to create a realistic production calendar, e.g.:

```
Monday    2:00–4:00 PM  Order #24 — Pattern development
          6:00–7:00 PM  Alteration #08
Tuesday   Unavailable — College classes
Wednesday 3:00–6:00 PM  Order #24 — Cutting + preparation
Thursday  2:00–6:00 PM  Order #24 — Construction
Saturday  11:00 AM–2:00 PM  Fabric sourcing
```

### Different Tasks Require Different Time Blocks

- **Long uninterrupted blocks** — pattern cutting, garment construction, draping, complex sewing.
- **Short blocks** — alterations, hand stitching, finishing, inventory updates, packaging, planning.
- **External blocks** — fabric shopping, material sourcing, customer meetings, deliveries.

This makes the calendar more realistic.

### Conflict Detection

The agent identifies problems before they become missed deadlines. Example: Order #24 requires 7 hours of production, but only 4.5 hours are available before its deadline. The agent explains the problem and proposes solutions: move another project, add a production session, source material earlier, reduce scope, change the delivery date, or prioritise the order over flexible projects.

### Rescheduling

The system reacts when plans change. Example: "I only completed one hour of Order #24 today instead of three." The agent recalculates remaining work, remaining available time, other deadlines, material dependencies, and college commitments, then proposes a new schedule. This creates a continuous planning system rather than a static calendar.

---

## 10. Garment Production Time Estimates

Realistic scheduling depends on knowing roughly how long each type of garment or task takes. The figures below are **starting baseline estimates** for a home/small-studio sewing workflow (design, pattern, cutting, construction, and finishing combined, single garment, moderate complexity). They are deliberately rough — the agent should treat them only as a fallback for new garment types, and should prefer numbers derived from the business owner's own **Past Project Database** (Section 15) whenever similar past projects exist.

| Garment / task | Estimated time | Notes |
|---|---|---|
| Simple alteration (hem, take in/out) | 0.5–1.5 hrs | Short-block task |
| Zip replacement | 0.5–1 hr | Short-block task |
| Sleeve alteration | 1–2 hrs | Short-block task |
| Basic skirt (straight/A-line, unlined) | 2–4 hrs | |
| Lined or fitted skirt | 4–6 hrs | |
| Basic top / blouse (simple pattern) | 3–5 hrs | |
| Fitted top with darts/closures | 5–7 hrs | |
| Corset / fully boned bodice | 8–14 hrs | Boning, structure, and fitting add time |
| Simple dress (unlined, basic silhouette) | 5–8 hrs | |
| Fitted dress (lined, structured bodice) | 10–16 hrs | |
| Two-piece outfit (fitted top + skirt) | 8–14 hrs | Roughly sum of the two components, minus shared fitting time |
| Trousers (tailored) | 6–10 hrs | |
| Jacket / blazer | 12–20 hrs | |
| Event/wedding gown | 20–40+ hrs | Highly variable; treat as its own estimation category |

**Suggested stage breakdown** (as a rough percentage of total estimated time, useful for building the session-by-session schedule):

- Design/pattern development: ~15%
- Cutting/preparation: ~15%
- Construction: ~55%
- Finishing/fitting: ~15%

**How the agent should use and improve these numbers:**

1. Use the table above only when there is no comparable past project.
2. Every time a project is completed, log **actual** hours spent per stage against the **estimated** hours (see Section 15).
3. Once a garment type has 3+ completed projects logged, the agent should compute a rolling average from history and use that instead of the baseline table — e.g. "Based on your last four corsets, I estimate roughly 9.5 hours: 1.5 for pattern, 1.5 for cutting, 5.5 for construction, 1 for finishing."
4. Flag garment types where actual time consistently overruns the estimate by a wide margin (a signal either to adjust the estimate or to re-quote/re-price that garment type).

---

## 11. AI Agent Setup & Involvement

The Tailoring Business Agent will use AI as the reasoning and orchestration layer of the system. The purpose of the AI is not simply to provide a conversational interface, but to understand the business owner's requests, identify which information is needed, and decide which actions or system functions should be used to solve the request.

For example, when the business owner asks "What should I work on today?" the agent should:

1. Check active orders and their deadlines.
2. Check the current production stage of each project.
3. Check estimated remaining work.
4. Check material availability and reservations.
5. Check the business owner's available time around college commitments.
6. Identify conflicts or urgent work.
7. Recommend what should be worked on and explain why.

The business owner should be able to interact with the system naturally rather than having to manually navigate between separate sections.

### AI Responsibilities

- Understanding natural language requests.
- Identifying the user's intended task.
- Selecting the appropriate agent skill or workflow.
- Reasoning across orders, materials, projects, available time, and marketing opportunities.
- Prioritising work based on multiple factors.
- Explaining why an order or task has been prioritised.
- Identifying missing information required to complete a task.
- Generating scheduling recommendations.
- Using previous projects to inform future recommendations.
- Suggesting possible garments based on available materials.
- Generating customer-facing catalogue and proposal content.
- Drafting Instagram captions and suggesting content based on current projects.
- Recommending next actions when problems or conflicts are detected.

### Deterministic System Responsibilities

Important business data and calculations should not depend entirely on AI judgement. The underlying system handles:

- Inventory quantities and units.
- Fractional material calculations.
- Reserved versus available stock.
- Material deductions and adjustments.
- Order and project status.
- Deadline and date calculations.
- Calendar availability.
- Recording completed work.
- Recording actual material usage.
- Maintaining the relationship between orders, projects and materials.
- Actually publishing a post to Instagram (only ever triggered after explicit approval — see Section 12).

This separation allows the agent to reason flexibly while keeping important business data predictable, traceable and reliable.

### Initial Agent Skills (MVP)

- **Order Management** — create, update and retrieve orders.
- **Inventory Check** — determine whether required materials are available.
- **Material Calculation** — calculate shortages and required quantities.
- **Priority Reasoning** — determine which order should be prioritised.
- **Production Planning** — identify available time for production.
- **Daily Planning** — answer "What should I work on today?"
- **Conflict Detection** — identify when deadlines, materials or available time create a problem.

Additional skills such as sourcing trip planning, historical project recommendations, customer catalogue generation, and Instagram/marketing integration will be developed after the core agent workflow is working.

### AI Involvement Level

**AI Involvement Level: High, with controlled system actions.**

A high level of AI involvement is appropriate because the central problem is not simply storing business information — the agent needs to reason across different types of information and determine what should happen next.

However, AI will not be responsible for exact inventory arithmetic, permanent database changes, or other operations where predictable results are important (including actually publishing content externally). These will be handled by deterministic system logic and confirmed by the business owner where appropriate.

---

## 12. Human-in-the-Loop Principle

The agent will recommend and plan, but the business owner remains responsible for approving important decisions.

For example, the agent may recommend: *"Work on Order #024 for two hours this afternoon because it has the closest deadline and all required materials are available."* The business owner can then approve, modify, or reject the recommendation.

**The user should approve:**

- New customer orders
- Significant schedule changes
- Material purchases
- Customer-facing proposals
- Inventory corrections
- Final customer communication
- **Any Instagram/social media post before it is published**, and specifically confirmation that a customer's custom order is cleared to be shown publicly before any related photo is posted

This keeps the system useful without allowing an AI model to make irreversible business or public-facing decisions without review.

---

## 13. Instagram Connection & Marketing Automation

A dedicated capability connects the agent to the business's Instagram presence, so that marketing stays connected to what is actually happening in production instead of being planned separately.

### What the agent should do

- **Connect to the Instagram account** (via the Instagram Graph API / Meta Business API, through a proper connected app rather than shared personal login credentials) to read basic account/content info and, once approved, publish posts.
- **Draft posts from current production activity** — e.g. when a project moves to a new stage (cutting, construction, finished/reveal), the agent can propose a caption and select from the project's progress photos.
- **Respect customer privacy and approval status** — the agent should never suggest posting a photo of a custom order unless that order's "shareable" flag (Section 05) is set and, where relevant, the customer has agreed to a public reveal. Date-sensitive customer orders (e.g. a surprise outfit) should be flagged as "hold until after [date]."
- **Promote from current inventory** — when the agent identifies underused or soon-to-expire-relevance fabric (e.g. seasonal stock, low-rotation fabric with high available quantity), it can suggest a promotional post inviting exploratory orders using that material — directly tying inventory management to marketing.
- **Build a content calendar** that sits alongside the production calendar, so posting suggestions are spaced out sensibly and don't clash with busy production/college periods.
- **Draft captions in the business's voice** — the agent should learn tone/style from previously approved captions rather than generating generic marketing copy.
- **Suggest hashtags and posting times** based on general best practice, refined over time using whatever basic performance data the Instagram API exposes (likes/comments/reach), feeding into "what type of content resonates" as part of the historical analysis skill.
- **Tie finished-project posts back to the customer catalogue system** — a well-received finished garment becomes a candidate to include in future customer inspiration PDFs (Section 16).

### What stays deterministic / human-controlled

- The agent **drafts**, it does not auto-publish. Every post requires explicit approval before it goes live (see Section 12).
- Scheduling the actual publish time/date, once approved, is a deterministic action (API call at the scheduled time), not an AI judgement call.
- Any customer-identifying information (name, specific delivery date, address, price) is excluded from generated captions by default.

### New data model entity: Marketing Post

| Field | Description |
|---|---|
| Post ID | Unique identifier |
| Linked order/project (optional) | Which project this content relates to |
| Draft caption | AI-drafted, editable text |
| Media | Selected image(s)/photo(s) |
| Status | Draft → Awaiting approval → Approved → Scheduled → Posted |
| Approval | Who approved, and confirmation the underlying order is clear to share publicly |
| Scheduled date/time | When it should post |
| Platform | Instagram (extensible to others later) |
| Performance (post-publish) | Likes, comments, reach, saves — pulled back in for historical analysis |

---

## 14. Apple Calendar Integration

The final system should ideally connect production planning to the user's real calendar. The agent could create calendar events for: sewing sessions, cutting, pattern development, alterations, fabric shopping, customer meetings, pickup/delivery, project deadlines, and now also **approved Instagram post publish times**, so the whole week — production and marketing — lives in one calendar view.

Example calendar event:

```
Tailoring Business Agent — Order #024: Construction
Duration: 3 hours
Deadline: 18 October
Fabric: Black denim
Available: 3.2 m
Required: 2.5 m
Tasks: Assemble bodice · Attach zip · Construct skirt
References: Customer image · Garment sketch · Fabric image
```

The exact Apple Calendar integration can be treated as an advanced implementation layer. The MVP can generate standard calendar events/ICS output if direct Apple integration proves too technically restrictive.

---

## 15. Multimedia, Visual Inventory & Past Project Database

### Multimedia Order Records

Every project should be capable of storing multimedia: customer references, fabric photographs, sketches, moodboards, previous garments, progress photographs, finished garments, and optionally voice notes, short videos, measurements, and design references. This creates a visual project history — and doubles as the raw material for Instagram content (Section 13).

### Visual Fabric Inventory

Fabric inventory should ideally not be purely text-based. A fabric record could contain a photograph plus type, colour, quantity, reserved, available, what it was previously used for, and possible garments it suits — e.g.:

```
BLACK COTTON
Type: Cotton · Colour: Black
Quantity: 4.75 m · Reserved: 2.50 m · Available: 2.25 m
Previously used for: Corset #024 · Skirt #011
Possible garments: Corset · Structured skirt · Vest · Mini dress
```

### Past Project Database

Every completed project becomes historical data: garment type, fabric, quantity used, pattern, construction time (planned vs. actual, per stage — feeding Section 10), final result, customer feedback, photographs, design references, alterations, and issues encountered. Over time this becomes a personal design and production archive.

### Learning From Past Projects

Past data improves future planning. For example, if previous corsets consistently used 1.6–1.8 m of fabric, the agent uses this instead of a generic assumption: *"Based on your previous corset projects, I estimate approximately 1.7 m of this fabric."* This is especially valuable because the agent becomes increasingly specific to this business over time.

---

## 16. Customer Inspiration System

One of the advanced features is the ability to create a customer-facing catalogue. The user could say: *"Create an inspiration catalogue for a customer who wants a summer outfit."*

The agent checks current inventory, available quantities, past projects, previous garment designs, customer requirements, suitable fabrics, and feasible silhouettes, then generates a PDF.

**Example structure:**

```
Cover: "Summer Outfit Inspiration — Curated from fabrics currently available"

Option 01 — Blue Cotton Midi Dress
Fabric available: 3.2 m
Why it works: Enough fabric available, based on previous similar-quantity projects.
Reference: Previous blue cotton project
Possible direction: Fitted bodice with a flowing skirt.

Option 02 — Black Denim Corset + Skirt
Fabric available: 2.4 m
Previous reference: Denim corset project
```

### Feasibility Labels

The agent distinguishes between levels of confidence:

- **READY TO MAKE** — enough material available, design supported by previous data.
- **ADAPTABLE** — material available, but the design would require modification.
- **NEEDS ADDITIONAL MATERIAL** — some material available, more needs sourcing.
- **CONCEPT** — an inspirational idea not yet validated against inventory or production constraints.

This prevents the AI from presenting speculative ideas as guaranteed possibilities.

### Personalised Customer Catalogues

The catalogue can be tailored — e.g. a customer wants something for a summer wedding, prefers blue, and doesn't want floor-length. The agent filters the database and generates only relevant options, prioritising blue fabrics, appropriate silhouettes, available quantities, past successful designs, and suitable production requirements.

### Customer Proposal Generation

For each option: garment concept, fabric, available quantity, estimated material requirement, reference images, production complexity, estimated timeline (using Section 10's estimates), and optional price estimate. The customer receives a polished document rather than a collection of disconnected chat images.

---

## 17. Main Agent Skills

**Core**
1. Order Management
2. Order Prioritisation
3. Project Management
4. Materials Inventory
5. Material Allocation
6. Production Scheduling
7. College Schedule Management
8. Conflict Detection
9. Rescheduling

**Sourcing**
10. Material Sourcing
11. Shopping List Generation
12. Shopping Trip Planning
13. Material Requirement Calculation

**Intelligence**
14. Historical Project Analysis
15. Material Usage Estimation
16. Production Time Estimation
17. Stock Monitoring
18. Low-Stock Detection

**Customer**
19. Customer Inspiration
20. Design Suggestions
21. Customer Proposal Generation
22. PDF Catalogue Generation

**Communication**
23. Customer Message Drafting
24. Order Updates
25. Delivery/Pickup Reminders

**Marketing & Social Media**
26. Instagram Account Connection
27. Progress Post Drafting
28. Caption Generation
29. Content Calendar Planning
30. Available-Stock Promotion Suggestions
31. Post Performance Review (feeds Historical Project Analysis)

**Media**
32. Image Organisation
33. Fabric Image Classification
34. Project Image Organisation
35. Visual Catalogue Generation

---

## 18. Agent Inputs & Outputs

### Inputs

- **Manual input** — e.g. "Add a new order for a customer."
- **Structured input** — an order form (customer, order type, deadline, garment, materials, estimated hours).
- **Images** — fabric photographs, sketches, customer references.
- **Calendar** — college timetable, existing commitments.
- **Historical data** — completed projects, previous fabric usage, past orders.
- **Social performance data** — likes/comments/reach on past posts, via the Instagram API.

### Outputs

- **Information** — priority lists, inventory status, order status, material requirements.
- **Actions** — create/update orders, reserve materials, update inventory, generate shopping lists, create calendar events.
- **Planning** — production schedules, sourcing trips, weekly plans, rescheduling recommendations.
- **Multimedia** — customer inspiration boards, project pages, visual inventory, PDF catalogues.
- **Marketing** — draft Instagram posts/captions, a content calendar, performance summaries.

---

## 19. Proposed User Interface

- **Dashboard** — today's tasks, urgent orders, upcoming deadlines, low inventory, upcoming sourcing trips, available production time, and any drafted posts awaiting approval.
- **Orders** — Kanban/table view: New → Planned → In Progress → Waiting for Material → Finishing → Completed, filterable by date-restricted/exploratory/alterations/priority/customer/deadline.
- **Inventory** — visual/material database: material, photograph, quantity, reserved, available, location, associated projects.
- **Calendar** — combined view of college, sewing, sourcing, customer commitments, deadlines, and scheduled Instagram posts.
- **Projects** — each order gets its own project page: customer, design, references, materials, tasks, progress, photos, calendar, notes.
- **Marketing** — content calendar, draft posts awaiting approval, published post performance, and stock-promotion suggestions.
- **Agent** — a conversational interface where the user can ask things like: "What should I work on today?", "What do I need to buy?", "Can I accept this order?", "Why is Order #24 my highest priority?", "Show me what I can make with my current fabrics.", "Make a catalogue for this customer.", "What should I post about this week?"

---

## 20. Example End-to-End Workflows

### Order workflow

A customer sends: *"I need an outfit for October 20. I'd like a fitted top and skirt in a dark colour."*

1. Agent creates Order #042 — Type: Date-restricted, Deadline: 20 October.
2. Checks inventory → finds black cotton, 3.2 m available.
3. Checks historical projects → finds two previous black cotton projects with similar silhouettes.
4. Estimates 2.8 m required, ~9 hours production (using Section 10 baselines, refined by history).
5. Checks college schedule → 9 hours available before October 20 → feasible.
6. Builds a schedule: pattern development → cutting → construction → finishing/fitting → pickup.
7. Reserves 2.8 m black cotton (available drops to 0.4 m).
8. Generates a customer proposal showing possible versions of the outfit.

### Exploratory workflow

Customer says: *"I want something flowy in red."* Agent checks inventory (red cotton 2.2 m, red satin 0 m, burgundy chiffon 3.8 m), checks previous projects, identifies possible garments per fabric, and generates an inspiration PDF. Customer chooses a chiffon dress; the agent converts the exploratory order into a project and, if additional lining is needed, adds it to sourcing — combining with any other order that also needs lining into the next sourcing trip.

### Rescheduling workflow

User says: *"I couldn't sew yesterday."* Agent checks affected projects, checks the college calendar for free time, moves production sessions, checks whether other orders need to be displaced, and reports the result (e.g. "Order #042 remains on schedule. Order #037 has been moved from Thursday to Saturday afternoon.") The user approves or modifies the change.

### Marketing workflow (new)

Order #042's construction stage finishes with strong progress photos, and the order's "shareable" flag is set (customer agreed to a public reveal). The agent drafts an Instagram post: caption in the business's usual tone, no customer-identifying details, suggested hashtags, and a suggested time slot that doesn't clash with an already-busy week. The business owner reviews, edits the caption slightly, and approves. The post is scheduled and later published automatically at the approved time. A week later, the agent notes the post performed well and suggests featuring that garment style in the next customer inspiration catalogue.

---

## 21. Goals & Success Criteria

**Primary goal:** Reduce the mental overhead of running the business by letting the business owner ask natural questions and get answers grounded in her actual orders, stock, calendar, and marketing activity — instead of holding it all in her head or across spreadsheets/notes apps/social apps.

**Success looks like:**

- The business owner can start her day by asking "what should I work on today?" and get a real, actionable answer.
- No order is missed or under-resourced because fabric requirements weren't checked.
- Sourcing trips are batched instead of ad hoc, saving time and travel.
- College commitments are respected automatically when the agent proposes schedules.
- Past projects are searchable and reusable as inspiration/reference for new customer requests.
- Marketing content stays connected to real production activity instead of being planned separately, without ever posting anything the business owner hasn't approved.

**Non-goals (at least initially):**

- Full accounting/invoicing system (may integrate with an existing tool rather than replace it)
- E-commerce storefront
- Automated customer messaging without the business owner's review
- Automated Instagram posting without explicit approval per post

---

## 22. Scope: MVP vs Final Vision

### MVP

**Goal:** Create an agent that can manage orders and materials, prioritise production, and build a realistic production calendar around the user's available time.

**MVP features:**

- **Orders** — create, categorise, store deadlines, store estimated production time (using Section 10 baselines), track status.
- **Inventory** — fabric/material database, fractional quantities, reserved quantities, available quantities, manual updates.
- **Projects** — material requirements, project status, actual material usage.
- **Scheduling** — college availability, production sessions, priority-based scheduling, deadline awareness.
- **Agent** — answer planning questions, identify conflicts, generate schedules, generate sourcing requirements.
- **Core reasoning queries answered correctly:** "What should I work on today?", "Which order should I prioritise?", "Do I have enough fabric for this order?", "What needs to be purchased for order X?"
- **Conversational interface** (chat-based) as the primary way to interact — no polished UI needed yet.

**Explicitly deferred from MVP:** sourcing trip batching/route optimisation, full historical project search/design recommendation engine, auto-generated garment catalogues, predictive rescheduling, Instagram/marketing integration, any customer-facing surface.

### Post-MVP Phases

**Phase 2**
- Automatic inventory reconciliation
- Shopping trip grouping
- Shopping list generation
- Historical project analysis (refining Section 10 estimates from real data)
- Material usage estimation
- Low-stock alerts

**Phase 3**
- Apple Calendar integration
- Multimedia inventory
- Project image organisation
- Customer proposal generation

**Phase 4**
- Instagram connection and content-calendar drafting (Section 13)
- Personalised inspiration PDFs
- Historical design recommendations
- Customer communication drafting
- Production analytics
- More autonomous rescheduling

### Final Vision

A personal operating system for the business, understanding the relationship between:

```
Customers → Orders → Projects → Materials → Inventory → Sourcing → Time →
College → Production → Completed garments → Historical knowledge →
Marketing → Future customer recommendations
```

The agent continuously uses this information to help make better decisions — production and marketing included.

---

## 23. What Makes It Agentic

The system should not require the user to manually tell it every step. For example, the user says: *"I have a new dress order due on the 25th."* The agent should determine that it needs to:

1. Create the order.
2. Determine its order category.
3. Ask for or identify missing information.
4. Estimate/record production requirements (Section 10).
5. Check materials.
6. Reserve available materials.
7. Identify missing materials.
8. Add missing materials to sourcing.
9. Check the college calendar.
10. Find production windows.
11. Prioritise the order.
12. Build a schedule.
13. Identify potential conflicts.
14. Present the resulting plan for approval.

The user provides the goal. The agent determines the workflow.

---

## 24. Success Criteria

The project should be considered successful if it can demonstrate that the agent can:

**Orders:** correctly categorise orders, identify urgent orders, track progress.

**Inventory:** store fractional quantities, track multiple material types, reserve materials, update quantities, maintain an inventory history.

**Scheduling:** understand available time, respect college commitments, prioritise deadlines, schedule realistic work blocks (using and improving on the estimates in Section 10), detect conflicts, reschedule when circumstances change.

**Sourcing:** identify missing materials, calculate quantities required, group materials into sourcing trips, generate shopping lists.

**Customer output:** use actual inventory, reference past projects, identify feasible garments, generate a polished inspiration PDF.

**Marketing:** draft on-brand Instagram content tied to real production milestones, never publish without approval, and respect per-order sharing/privacy status.

---

## 25. The Central Design Principle

The system should always answer:

> "Given everything I currently know, what is the best next action?"

Not simply:

> "What information do I have?"

This distinction is central to the project. The agent transforms information into action.

---

## 26. Final One-Line Description

The Tailoring Business Agent is an AI-powered production, business, and marketing management agent that connects orders, material inventory, sourcing, college schedules, historical projects, and Instagram activity to plan what should be made, when it should be made, what needs to be purchased, what can be offered to customers, and what should be shared publicly.

---

## 27. Short Pitch

The Tailoring Business Agent is a personal AI production manager for a custom fashion business. It organises orders by urgency and type, maintains a fractional inventory of fabrics and other materials, automatically accounts for material consumption, plans sourcing trips, schedules production around college commitments, adapts when plans change, uses current inventory and past projects to generate personalised customer inspiration catalogues, and drafts Instagram content tied to real production activity — all while keeping the business owner in control of anything that leaves the system (purchases, customer messages, and public posts).

---

## 28. Core System

```
ORDERS        What needs to be made?
   ↓
PRIORITY      What matters most?
   ↓
MATERIALS     Do I have what I need?
   ↓
SOURCING      What needs to be bought?
   ↓
TIME          When can I actually do it?
   ↓
SCHEDULE      What should I do and when?
   ↓
PRODUCTION    What was actually used?
   ↓
INVENTORY     What do I have now?
   ↓
HISTORY       What have I learnt?
   ↓
MARKETING     What's worth sharing right now?
   ↓
CUSTOMER      What can I offer next?
   ↓
AGENT         Continuously connects all of the above.
```
## ## Tailoring Business Agent — Project Plan


## 01. **Project Overview**

**Project Name:** Tailoring Business Agent; Project **Type:** AI Agent / Business Operations System **Domain:** Fashion Design, Custom Clothing, Small Business Operations Primary User: the business owner

**Core Problem:** Managing a small custom clothing business involves keeping track of customer orders, deadlines, fabrics and other materials, production time, sourcing trips, alterations, college commitments, and customer communication. These pieces of information are interconnected, but are often managed separately.

The Tailoring Business Agent is designed to bring these systems together. It acts as an intelligent production and business assistant that understands:

What orders exist
Which orders are urgent
What materials are available
Which materials are reserved
What needs to be sourced
What projects are currently being worked on
How much time each project requires
When college commitments make production unavailable
What needs to happen next
What materials could be used for future designs
What previous business owner projects can inform new recommendations

The agent then uses this information to plan and continuously update the business workflow.


## 02. **Core Concept**

Turn the information surrounding the business owner into one interconnected system that can reason about orders, materials, and time, rather than treating each as a separate database.

The system should answer questions such as:

What should I work on today?
Which order should I prioritise?
Do I have enough fabric for this order?
Which materials need to be purchased?
Can I combine these purchases into one sourcing trip?
When can I realistically complete this order around college?
What happens to my schedule if I don't finish today's work?
What do I currently have in my inventory?
What can I make from the fabric I currently own?
What have I made in the past using similar materials?
Can you make a catalogue of possible garments I can offer this customer?

The differentiator is not any single feature — it's that orders, materials, time, and history all sit in one connected model, so a question about "today's priorities" can pull from all four at once instead of requiring the business owner to check four separate tools and reconcile them manually.


## **03. AI Agent Setup & Involvement**

The Tailoring Business Agent will use AI as the reasoning and orchestration layer of the system. The purpose of the AI is not simply to provide a conversational interface, but to understand the business owner's requests, identify which information is needed, and decide which actions or system functions should be used to solve the request.

For example, when the business owner asks:

> "What should I work on today?"

the agent should be able to:

1. Check active orders and their deadlines.
2. Check the current production stage of each project.
3. Check estimated remaining work.
4. Check material availability and reservations.
5. Check the business owner's available time around college commitments.
6. Identify conflicts or urgent work.
7. Recommend what should be worked on and explain why.

The business owner should be able to interact with the system naturally rather than having to manually navigate between separate sections.

**AI Responsibilities**

The AI will be responsible for:

* Understanding natural language requests.
* Identifying the user's intended task.
* Selecting the appropriate agent skill or workflow.
* Reasoning across orders, materials, projects and available time.
* Prioritising work based on multiple factors.
* Explaining why an order or task has been prioritised.
* Identifying missing information required to complete a task.
* Generating scheduling recommendations.
* Using previous projects to inform future recommendations.
* Suggesting possible garments based on available materials.
* Generating customer-facing catalogue and proposal content.
* Recommending next actions when problems or conflicts are detected.

**Deterministic System Responsibilities**

Important business data and calculations should not depend entirely on AI judgement. The underlying system will handle:

* Inventory quantities and units.
* Fractional material calculations.
* Reserved versus available stock.
* Material deductions and adjustments.
* Order and project status.
* Deadline and date calculations.
* Calendar availability.
* Recording completed work.
* Recording actual material usage.
* Maintaining the relationship between orders, projects and materials.

This separation allows the agent to reason flexibly while keeping important business data predictable, traceable and reliable.

**Initial Agent Skills**

The initial setup will establish the core skills required for the MVP:

* Order Management: create, update and retrieve orders.
* Inventory Check: determine whether required materials are available.
* Material Calculation: calculate shortages and required quantities.
* Priority Reasoning: determine which order should be prioritised.
* Production Planning: identify available time for production.
* Daily Planning: answer "What should I work on today?"
* Conflict Detection: identify when deadlines, materials or available time create a problem.

Additional skills such as sourcing trip planning, historical project recommendations and customer catalogue generation will be developed after the core agent workflow is working.

### Human-in-the-Loop

The agent will recommend and plan, but the business owner remains responsible for approving important decisions.

For example, the agent may recommend:

> "Work on Order #024 for two hours this afternoon because it has the closest deadline and all required materials are available."

The business owner can then approve, modify or reject the recommendation.

This keeps the system useful without allowing an AI model to make irreversible business decisions without review.

### AI Involvement Level

**AI Involvement Level: High, with controlled system actions.**

A high level of AI involvement is appropriate because the central problem is not simply storing business information. The agent needs to reason across different types of information and determine what should happen next.

However, AI will not be responsible for exact inventory arithmetic, permanent database changes or other operations where predictable results are important. These will be handled by deterministic system logic and confirmed by the business owner where appropriate.


## 04. **Goals & Success Criteria**

Primary goal: Reduce the mental overhead of running the business by letting the business owner ask natural questions and get answers grounded in her actual orders, stock, and calendar — instead of holding it all in her head or across spreadsheets/notes apps.

Success looks like:

The business owner can start her day by asking "what should I work on today?" and get a real, actionable answer.
No order is missed or under-resourced because fabric requirements weren't checked.
Sourcing trips are batched instead of ad hoc, saving time and travel.
College commitments are respected automatically when the agent proposes schedules.
Past projects are searchable and reusable as inspiration/reference for new customer requests.

Non-goals (at least initially):

Full accounting/invoicing system (may integrate with an existing tool rather than replace it)
E-commerce storefront
Automated customer messaging without the business owner's review


## 05. **Scope: MVP vs Final Vision**

MVP (Minimum Viable Product)

**Goal:** prove the core loop — orders + materials + time in one place, with the agent able to reason across them.

**MVP includes:**

Data model for four core entities: Orders, Materials/Inventory, Projects (production units tied to orders), and a Calendar/Commitments layer (college schedule + blocked time).
Manual or lightweight data entry — the business owner (or the agent, conversationally) adds/updates orders, materials, and commitments.
Core reasoning queries answered correctly:
"What should I work on today?"
"Which order should I prioritise?"
"Do I have enough fabric for this order?"
"What needs to be purchased for order X?"
Simple urgency/priority logic based on deadline, remaining production time, and material availability.
Basic material shortage detection — flags what's missing per order and produces a combined shortage list across open orders.
A conversational interface (chat-based) as the primary way to interact with the system — no need for a polished UI yet.

**Explicitly deferred from MVP:**

Sourcing trip batching/route optimization
Full historical project search / design recommendation engine
Auto-generated garment catalogues
Predictive scheduling ("what happens if I don't finish today")
Any customer-facing surface
Final Vision (Full Scope)

Everything above, plus:

Sourcing trip planning — combine shortages across multiple orders into a single optimized shopping list/trip.
Time-aware scheduling — the agent proposes a realistic day-by-day/week-by-week plan around college commitments, and can re-plan when a day is missed ("what happens to my schedule if I don't finish today's work?").
Historical project memory — a searchable archive of past business owner projects (fabric used, techniques, customer, outcome) that informs new recommendations ("what have I made in the past using similar materials?").
Inventory-driven design suggestions — "what can I make from the fabric I currently own?" using a library of patterns/techniques matched against on-hand materials.
Catalogue generation — auto-drafted garment catalogues per customer, based on their preferences, budget, and the business owner's available materials/techniques.
Proactive notifications — the agent flags risks before they're urgent (e.g., "Order #12 needs fabric you don't have, and your college exams start in 5 days").
Light customer communication support — drafts (not auto-sends) status updates or quote messages for the business owner to review and send.
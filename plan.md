Tailoring Business Agent — Project Plan
01. Project Overview

Project Name: Tailoring Business Agent; Project Type: AI Agent / Business Operations System Domain: Fashion Design, Custom Clothing, Small Business Operations Primary User: the business owner

Core Problem: Managing a small custom clothing business involves keeping track of customer orders, deadlines, fabrics and other materials, production time, sourcing trips, alterations, college commitments, and customer communication. These pieces of information are interconnected, but are often managed separately.

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

02. Core Concept

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

03. Goals & Success Criteria

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
04. Scope: MVP vs Final Vision
MVP (Minimum Viable Product)

Goal: prove the core loop — orders + materials + time in one place, with the agent able to reason across them.

MVP includes:

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

Explicitly deferred from MVP:

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

# conference-helpdesk
An AI-powered conference assistant that answers attendee questions about sessions, schedules, speakers, and venues. Users can have continuous conversations and generate a personalized summary of their interactions at the end.

# Tech

System 1: Conference Data Ingestion System
Collect and index conference information.
<img width="508" height="922" alt="mermaid-diagram (1)" src="https://github.com/user-attachments/assets/f0b54a6a-3a28-4210-b6c0-5b959372647c" />

Purpose: Automatically collect conference schedules, sessions, speakers, venues, FAQs and other information, then index it in Elasticsearch.

System 2: Conference Helpdesk AI
Answer attendee questions and generate summaries.
<img width="1166" height="1552" alt="mermaid-diagram (2)" src="https://github.com/user-attachments/assets/4fb679df-f307-483c-b850-571e5ed0cb8c" />

Purpose: Allow attendees to ask questions in natural language, receive answers based on indexed conference information, and get a summary of their conversation at the end.

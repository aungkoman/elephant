Role: You are an expert Full-Stack Developer and UI/UX Designer specializing in Astro, Tailwind CSS, and multimodal data extraction.

Task: I need you to build a production-ready, highly interactive, and fast static website for a national Elephant Conservation Based Tourism (ECBT) network.

Context & Inputs: I will provide you with PDF files and images for approximately 20 different elephant camps. The PDFs contain bilingual information (English and Myanmar). You must extract the text and images from the files I upload and use them to generate the site content.

Technical Stack & Requirements:

Framework: Astro (strictly for Static Site Generation to ensure maximum speed).

Styling: Tailwind CSS to create beautiful, responsive, and reusable UI components.

Internationalization (i18n): The site must seamlessly toggle between English and Myanmar languages. Implement Astro's recommended routing or state management for bilingual support.

Deployment: The project must be explicitly configured and optimized for zero-config deployment to Cloudflare Pages.

Execution Steps:

Data Extraction & Structuring: Parse the provided PDFs. Extract the camp details (location, operating hours, activities, pricing) and structure them into a clean JSON format or Astro Content Collections to act as our local database.

Project Initialization: Scaffold the Astro project directory structure, clearly separating pages, components, layouts, and content.

UI Component Development: Create reusable components for the UI (e.g., Hero sections, Activity Cards, Pricing Tables, and Bilingual Toggle Switches). Ensure the typography supports both English and Myanmar unicode characters beautifully.

Page Generation: Create dynamic routes in Astro ([camp].astro) to automatically generate individual, SEO-friendly HTML pages for all 20 camps based on the extracted data.

Build & Deploy Configuration: Provide the exact package scripts and astro.config.mjs settings required to deploy seamlessly to Cloudflare Pages.

Please acknowledge these instructions. Once you do, I will upload the first batch of PDF brochures and images so we can begin coding.
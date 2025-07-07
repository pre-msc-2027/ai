#!/usr/bin/env python3
"""
Create a test frontend workspace with a realistic HTML/CSS/JS project structure
for testing cli_workspace.py
"""

import os
from pathlib import Path


def create_frontend_workspace():
    """Create a comprehensive frontend test workspace structure"""

    # Base directory
    base_dir = Path("test_workspaces") / "frontend_workspace"

    # Create directory structure
    directories = [
        "src",
        "src/css",
        "src/js",
        "src/images",
        "src/components",
        "public",
        "docs",
        "tests",
        ".github/workflows",
    ]

    for dir_path in directories:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)

    # Create files with content
    files = {
        # Root files
        "README.md": """# Frontend Test Project

A modern, responsive website built with HTML5, CSS3, and vanilla JavaScript.

## Features
- Responsive design
- Modern CSS Grid and Flexbox
- Interactive components
- Accessibility focused
- SEO optimized

## Structure
- `src/` - Source files
- `public/` - Static assets and build output
- `docs/` - Documentation
- `tests/` - Test files

## Getting Started
1. Open `public/index.html` in your browser
2. Or serve with a local server: `python -m http.server 8000`
3. Navigate to `http://localhost:8000/public/`

## Development
- Edit HTML in `public/`
- Edit CSS in `src/css/`
- Edit JavaScript in `src/js/`
- Images go in `src/images/`
""",
        "package.json": """{
  "name": "frontend-test-project",
  "version": "1.0.0",
  "description": "A test frontend project for workspace management",
  "main": "public/index.html",
  "scripts": {
    "start": "python -m http.server 8000",
    "build": "echo 'No build process defined'",
    "test": "echo 'No tests defined'"
  },
  "keywords": ["html", "css", "javascript", "frontend"],
  "author": "Test Developer",
  "license": "MIT"
}""",
        ".gitignore": """# OS files
.DS_Store
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
npm-debug.log*

# Runtime data
pids
*.pid
*.seed

# Coverage directory used by tools like istanbul
coverage/

# Dependency directories
node_modules/

# Optional npm cache directory
.npm

# Build outputs
dist/
build/
""",
        # Public HTML files
        "public/index.html": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Page d'accueil du projet frontend de test">
    <title>Frontend Test Project - Accueil</title>
    <link rel="stylesheet" href="../src/css/main.css">
    <link rel="stylesheet" href="../src/css/components.css">
    <link rel="icon" href="../src/images/favicon.ico">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <h1>Frontend Test</h1>
                </div>
                <ul class="navbar-nav">
                    <li><a href="index.html" class="nav-link active">Accueil</a></li>
                    <li><a href="about.html" class="nav-link">À propos</a></li>
                    <li><a href="portfolio.html" class="nav-link">Portfolio</a></li>
                    <li><a href="contact.html" class="nav-link">Contact</a></li>
                </ul>
                <button class="mobile-toggle" aria-label="Toggle navigation">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </nav>
    </header>

    <main class="main">
        <section class="hero">
            <div class="container">
                <div class="hero-content">
                    <h2>Bienvenue sur notre site de test</h2>
                    <p>Un projet frontend moderne pour tester les outils de gestion de workspace.</p>
                    <div class="hero-buttons">
                        <a href="portfolio.html" class="btn btn-primary">Voir le portfolio</a>
                        <a href="contact.html" class="btn btn-secondary">Nous contacter</a>
                    </div>
                </div>
            </div>
        </section>

        <section class="features">
            <div class="container">
                <h2>Fonctionnalités</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>Responsive Design</h3>
                        <p>Interface adaptée à tous les écrans et appareils.</p>
                    </div>
                    <div class="feature-card">
                        <h3>CSS Moderne</h3>
                        <p>Utilisation de Grid, Flexbox et variables CSS.</p>
                    </div>
                    <div class="feature-card">
                        <h3>JavaScript Interactif</h3>
                        <p>Composants dynamiques et interactions utilisateur.</p>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Frontend Test Project. Tous droits réservés.</p>
        </div>
    </footer>

    <script src="../src/js/main.js"></script>
    <script src="../src/js/components.js"></script>
</body>
</html>""",
        "public/about.html": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="À propos du projet frontend de test">
    <title>Frontend Test Project - À propos</title>
    <link rel="stylesheet" href="../src/css/main.css">
    <link rel="stylesheet" href="../src/css/components.css">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <h1>Frontend Test</h1>
                </div>
                <ul class="navbar-nav">
                    <li><a href="index.html" class="nav-link">Accueil</a></li>
                    <li><a href="about.html" class="nav-link active">À propos</a></li>
                    <li><a href="portfolio.html" class="nav-link">Portfolio</a></li>
                    <li><a href="contact.html" class="nav-link">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>

    <main class="main">
        <section class="about-hero">
            <div class="container">
                <h2>À propos du projet</h2>
                <p class="lead">Ce projet sert de workspace de test pour les outils de gestion de fichiers avec l'IA.</p>
            </div>
        </section>

        <section class="about-content">
            <div class="container">
                <div class="content-grid">
                    <div class="content-text">
                        <h3>Notre mission</h3>
                        <p>Créer un environnement de test réaliste pour valider les fonctionnalités de gestion de workspace avec Ollama.</p>

                        <h3>Technologies utilisées</h3>
                        <ul>
                            <li>HTML5 sémantique</li>
                            <li>CSS3 avec Grid et Flexbox</li>
                            <li>JavaScript vanilla</li>
                            <li>Design responsive</li>
                        </ul>
                    </div>
                    <div class="content-image">
                        <div class="placeholder-image">
                            <p>Image placeholder</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Frontend Test Project. Tous droits réservés.</p>
        </div>
    </footer>

    <script src="../src/js/main.js"></script>
</body>
</html>""",
        "public/portfolio.html": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Portfolio du projet frontend de test">
    <title>Frontend Test Project - Portfolio</title>
    <link rel="stylesheet" href="../src/css/main.css">
    <link rel="stylesheet" href="../src/css/components.css">
    <link rel="stylesheet" href="../src/css/portfolio.css">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <h1>Frontend Test</h1>
                </div>
                <ul class="navbar-nav">
                    <li><a href="index.html" class="nav-link">Accueil</a></li>
                    <li><a href="about.html" class="nav-link">À propos</a></li>
                    <li><a href="portfolio.html" class="nav-link active">Portfolio</a></li>
                    <li><a href="contact.html" class="nav-link">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>

    <main class="main">
        <section class="portfolio-hero">
            <div class="container">
                <h2>Notre Portfolio</h2>
                <p>Découvrez nos projets et réalisations.</p>
            </div>
        </section>

        <section class="portfolio-gallery">
            <div class="container">
                <div class="portfolio-filters">
                    <button class="filter-btn active" data-filter="all">Tous</button>
                    <button class="filter-btn" data-filter="web">Web</button>
                    <button class="filter-btn" data-filter="mobile">Mobile</button>
                    <button class="filter-btn" data-filter="design">Design</button>
                </div>

                <div class="portfolio-grid">
                    <div class="portfolio-item" data-category="web">
                        <div class="portfolio-image">
                            <div class="placeholder-image">Projet Web 1</div>
                        </div>
                        <div class="portfolio-info">
                            <h3>Site E-commerce</h3>
                            <p>Développement d'une boutique en ligne responsive.</p>
                        </div>
                    </div>

                    <div class="portfolio-item" data-category="mobile">
                        <div class="portfolio-image">
                            <div class="placeholder-image">App Mobile 1</div>
                        </div>
                        <div class="portfolio-info">
                            <h3>Application Mobile</h3>
                            <p>Interface utilisateur pour application iOS/Android.</p>
                        </div>
                    </div>

                    <div class="portfolio-item" data-category="design">
                        <div class="portfolio-image">
                            <div class="placeholder-image">Design 1</div>
                        </div>
                        <div class="portfolio-info">
                            <h3>Identité Visuelle</h3>
                            <p>Création d'une charte graphique complète.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Frontend Test Project. Tous droits réservés.</p>
        </div>
    </footer>

    <script src="../src/js/main.js"></script>
    <script src="../src/js/portfolio.js"></script>
</body>
</html>""",
        "public/contact.html": """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Contactez-nous - Frontend Test Project">
    <title>Frontend Test Project - Contact</title>
    <link rel="stylesheet" href="../src/css/main.css">
    <link rel="stylesheet" href="../src/css/components.css">
    <link rel="stylesheet" href="../src/css/forms.css">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <h1>Frontend Test</h1>
                </div>
                <ul class="navbar-nav">
                    <li><a href="index.html" class="nav-link">Accueil</a></li>
                    <li><a href="about.html" class="nav-link">À propos</a></li>
                    <li><a href="portfolio.html" class="nav-link">Portfolio</a></li>
                    <li><a href="contact.html" class="nav-link active">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>

    <main class="main">
        <section class="contact-hero">
            <div class="container">
                <h2>Contactez-nous</h2>
                <p>N'hésitez pas à nous contacter pour vos projets.</p>
            </div>
        </section>

        <section class="contact-content">
            <div class="container">
                <div class="contact-grid">
                    <div class="contact-info">
                        <h3>Informations de contact</h3>
                        <div class="contact-item">
                            <strong>Email:</strong>
                            <p>contact@frontend-test.com</p>
                        </div>
                        <div class="contact-item">
                            <strong>Téléphone:</strong>
                            <p>+33 1 23 45 67 89</p>
                        </div>
                        <div class="contact-item">
                            <strong>Adresse:</strong>
                            <p>123 Rue de Test<br>75001 Paris, France</p>
                        </div>
                    </div>

                    <div class="contact-form">
                        <form id="contactForm" class="form">
                            <div class="form-group">
                                <label for="name">Nom complet</label>
                                <input type="text" id="name" name="name" required>
                            </div>

                            <div class="form-group">
                                <label for="email">Email</label>
                                <input type="email" id="email" name="email" required>
                            </div>

                            <div class="form-group">
                                <label for="subject">Sujet</label>
                                <input type="text" id="subject" name="subject" required>
                            </div>

                            <div class="form-group">
                                <label for="message">Message</label>
                                <textarea id="message" name="message" rows="5" required></textarea>
                            </div>

                            <button type="submit" class="btn btn-primary">Envoyer le message</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Frontend Test Project. Tous droits réservés.</p>
        </div>
    </footer>

    <script src="../src/js/main.js"></script>
    <script src="../src/js/contact.js"></script>
</body>
</html>""",
        # CSS files
        "src/css/main.css": """/* CSS Variables */
:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --accent-color: #e74c3c;
    --text-color: #333;
    --text-light: #777;
    --bg-color: #fff;
    --bg-light: #f8f9fa;
    --border-color: #ddd;
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    --border-radius: 8px;
    --transition: all 0.3s ease;
}

/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    margin-bottom: 1rem;
    font-weight: 600;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }

p {
    margin-bottom: 1rem;
}

.lead {
    font-size: 1.2rem;
    font-weight: 300;
    color: var(--text-light);
}

/* Header */
.header {
    background: var(--bg-color);
    box-shadow: var(--shadow);
    position: sticky;
    top: 0;
    z-index: 100;
}

.navbar {
    padding: 1rem 0;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-brand h1 {
    color: var(--primary-color);
    margin: 0;
}

.navbar-nav {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-link {
    text-decoration: none;
    color: var(--text-color);
    font-weight: 500;
    transition: var(--transition);
    padding: 0.5rem 1rem;
    border-radius: var(--border-radius);
}

.nav-link:hover,
.nav-link.active {
    color: var(--primary-color);
    background: var(--bg-light);
}

.mobile-toggle {
    display: none;
    flex-direction: column;
    background: none;
    border: none;
    cursor: pointer;
    gap: 4px;
}

.mobile-toggle span {
    width: 25px;
    height: 3px;
    background: var(--text-color);
    transition: var(--transition);
}

/* Main Content */
.main {
    min-height: calc(100vh - 200px);
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 4rem 0;
    text-align: center;
}

.hero-content h2 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.hero-content p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.hero-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 24px;
    text-decoration: none;
    border-radius: var(--border-radius);
    font-weight: 500;
    text-align: center;
    transition: var(--transition);
    border: none;
    cursor: pointer;
    font-size: 1rem;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
    transform: translateY(-2px);
}

.btn-secondary {
    background: transparent;
    color: white;
    border: 2px solid white;
}

.btn-secondary:hover {
    background: white;
    color: var(--primary-color);
}

/* Features Section */
.features {
    padding: 4rem 0;
    background: var(--bg-light);
}

.features h2 {
    text-align: center;
    margin-bottom: 3rem;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    text-align: center;
    transition: var(--transition);
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* Footer */
.footer {
    background: var(--secondary-color);
    color: white;
    text-align: center;
    padding: 2rem 0;
    margin-top: auto;
}

/* Responsive Design */
@media (max-width: 768px) {
    .navbar-nav {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        flex-direction: column;
        padding: 1rem;
        box-shadow: var(--shadow);
    }

    .navbar-nav.active {
        display: flex;
    }

    .mobile-toggle {
        display: flex;
    }

    .hero-content h2 {
        font-size: 2rem;
    }

    .hero-buttons {
        flex-direction: column;
        align-items: center;
    }

    .container {
        padding: 0 15px;
    }
}

/* Utility Classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.mt-1 { margin-top: 1rem; }
.mt-2 { margin-top: 2rem; }
.mb-1 { margin-bottom: 1rem; }
.mb-2 { margin-bottom: 2rem; }

.p-1 { padding: 1rem; }
.p-2 { padding: 2rem; }
""",
        "src/css/components.css": """/* About Page Styles */
.about-hero {
    background: var(--bg-light);
    padding: 3rem 0;
    text-align: center;
}

.about-content {
    padding: 4rem 0;
}

.content-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 3rem;
    align-items: start;
}

.content-text h3 {
    color: var(--primary-color);
    margin-top: 2rem;
}

.content-text ul {
    margin-left: 2rem;
}

.content-text li {
    margin-bottom: 0.5rem;
}

.placeholder-image {
    background: var(--bg-light);
    border: 2px dashed var(--border-color);
    border-radius: var(--border-radius);
    padding: 4rem 2rem;
    text-align: center;
    color: var(--text-light);
    font-style: italic;
}

/* Contact Page Styles */
.contact-hero {
    background: var(--bg-light);
    padding: 3rem 0;
    text-align: center;
}

.contact-content {
    padding: 4rem 0;
}

.contact-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
}

.contact-info h3 {
    color: var(--primary-color);
    margin-bottom: 2rem;
}

.contact-item {
    margin-bottom: 2rem;
}

.contact-item strong {
    color: var(--secondary-color);
    display: block;
    margin-bottom: 0.5rem;
}

/* Portfolio Page Styles */
.portfolio-hero {
    background: var(--bg-light);
    padding: 3rem 0;
    text-align: center;
}

.portfolio-gallery {
    padding: 4rem 0;
}

.portfolio-filters {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-bottom: 3rem;
    flex-wrap: wrap;
}

.filter-btn {
    background: transparent;
    border: 2px solid var(--primary-color);
    color: var(--primary-color);
    padding: 0.5rem 1.5rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    transition: var(--transition);
    font-weight: 500;
}

.filter-btn:hover,
.filter-btn.active {
    background: var(--primary-color);
    color: white;
}

.portfolio-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.portfolio-item {
    background: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    overflow: hidden;
    transition: var(--transition);
}

.portfolio-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.portfolio-image {
    height: 200px;
    overflow: hidden;
}

.portfolio-image .placeholder-image {
    height: 100%;
    border: none;
    border-radius: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
}

.portfolio-info {
    padding: 1.5rem;
}

.portfolio-info h3 {
    color: var(--secondary-color);
    margin-bottom: 0.5rem;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .content-grid,
    .contact-grid {
        grid-template-columns: 1fr;
        gap: 2rem;
    }

    .portfolio-filters {
        gap: 0.5rem;
    }

    .filter-btn {
        padding: 0.4rem 1rem;
        font-size: 0.9rem;
    }
}
""",
        "src/css/forms.css": """/* Form Styles */
.form {
    background: white;
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--secondary-color);
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 12px;
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius);
    font-size: 1rem;
    transition: var(--transition);
    font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.form-group textarea {
    resize: vertical;
    min-height: 120px;
}

/* Form Validation */
.form-group input:invalid,
.form-group textarea:invalid {
    border-color: var(--accent-color);
}

.form-group input:valid,
.form-group textarea:valid {
    border-color: #27ae60;
}

/* Error and Success States */
.form-error {
    color: var(--accent-color);
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

.form-success {
    color: #27ae60;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* Checkbox and Radio Styles */
.form-check {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.form-check input[type="checkbox"],
.form-check input[type="radio"] {
    width: auto;
    margin: 0;
}

/* Custom Select Arrow */
select {
    background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='%23333' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    background-size: 16px;
    appearance: none;
    padding-right: 40px;
}

/* Responsive Form Adjustments */
@media (max-width: 768px) {
    .form {
        padding: 1.5rem;
    }
}
""",
        "src/css/portfolio.css": """/* Additional Portfolio Styles */
.portfolio-item.hidden {
    display: none;
}

.portfolio-item.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Portfolio Modal */
.portfolio-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}

.portfolio-modal.active {
    display: flex;
}

.modal-content {
    background: white;
    max-width: 800px;
    max-height: 90vh;
    border-radius: var(--border-radius);
    padding: 2rem;
    position: relative;
    overflow-y: auto;
}

.modal-close {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: none;
    border: none;
    font-size: 2rem;
    cursor: pointer;
    color: var(--text-light);
}

.modal-close:hover {
    color: var(--text-color);
}

/* Portfolio Categories */
.portfolio-category {
    display: inline-block;
    background: var(--bg-light);
    color: var(--text-color);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    margin: 0.25rem;
}

/* Loading State */
.portfolio-loading {
    text-align: center;
    padding: 3rem;
    color: var(--text-light);
}

.portfolio-loading::after {
    content: '';
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid var(--border-color);
    border-top: 2px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-left: 10px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
""",
        # JavaScript files
        "src/js/main.js": """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend Test Project loaded');

    // Mobile navigation toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navbarNav = document.querySelector('.navbar-nav');

    if (mobileToggle && navbarNav) {
        mobileToggle.addEventListener('click', function() {
            navbarNav.classList.toggle('active');
            mobileToggle.classList.toggle('active');
        });
    }

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading class to body
    document.body.classList.add('loaded');

    // Simple animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animateElements = document.querySelectorAll('.feature-card, .portfolio-item');
    animateElements.forEach(el => observer.observe(el));
});

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: slideInUp 0.6s ease-out;
    }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);
""",
        "src/js/components.js": """// Reusable components
class Modal {
    constructor(selector) {
        this.modal = document.querySelector(selector);
        this.closeBtn = this.modal?.querySelector('.modal-close');
        this.init();
    }

    init() {
        if (!this.modal) return;

        // Close on close button click
        this.closeBtn?.addEventListener('click', () => this.close());

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.close();
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) this.close();
        });
    }

    open() {
        this.modal?.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.modal?.classList.remove('active');
        document.body.style.overflow = '';
    }

    isOpen() {
        return this.modal?.classList.contains('active');
    }
}

// Notification system
class NotificationSystem {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: white;
            border-left: 4px solid ${this.getColor(type)};
            padding: 1rem;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        notification.textContent = message;

        this.container.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                this.container.removeChild(notification);
            }, 300);
        }, duration);
    }

    getColor(type) {
        const colors = {
            success: '#27ae60',
            error: '#e74c3c',
            warning: '#f39c12',
            info: '#3498db'
        };
        return colors[type] || colors.info;
    }
}

// Form validator
class FormValidator {
    constructor(form) {
        this.form = form;
        this.rules = {};
        this.init();
    }

    init() {
        if (!this.form) return;

        this.form.addEventListener('submit', (e) => {
            if (!this.validate()) {
                e.preventDefault();
            }
        });

        // Real-time validation
        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
        });
    }

    addRule(fieldName, validator, message) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = [];
        }
        this.rules[fieldName].push({ validator, message });
    }

    validate() {
        let isValid = true;

        Object.keys(this.rules).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field && !this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const fieldName = field.name;
        const rules = this.rules[fieldName];

        if (!rules) return true;

        let isValid = true;
        this.clearFieldError(field);

        for (const rule of rules) {
            if (!rule.validator(field.value)) {
                this.showFieldError(field, rule.message);
                isValid = false;
                break;
            }
        }

        return isValid;
    }

    showFieldError(field, message) {
        field.classList.add('error');
        const errorEl = document.createElement('div');
        errorEl.className = 'form-error';
        errorEl.textContent = message;
        field.parentNode.appendChild(errorEl);
    }

    clearFieldError(field) {
        field.classList.remove('error');
        const existingError = field.parentNode.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
    }
}

// Initialize global components
const notifications = new NotificationSystem();

// Export for use in other files
window.Modal = Modal;
window.notifications = notifications;
window.FormValidator = FormValidator;
""",
        "src/js/portfolio.js": """// Portfolio page specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const portfolioContainer = document.querySelector('.portfolio-grid');
    const filterButtons = document.querySelectorAll('.filter-btn');

    if (!portfolioContainer || !filterButtons.length) return;

    // Portfolio filtering
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.dataset.filter;

            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // Filter portfolio items
            filterPortfolioItems(filter);
        });
    });

    function filterPortfolioItems(filter) {
        const items = portfolioContainer.querySelectorAll('.portfolio-item');

        items.forEach(item => {
            const category = item.dataset.category;

            if (filter === 'all' || category === filter) {
                item.style.display = 'block';
                item.classList.add('fade-in');
            } else {
                item.style.display = 'none';
                item.classList.remove('fade-in');
            }
        });
    }

    // Portfolio item click handlers
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    portfolioItems.forEach(item => {
        item.addEventListener('click', function() {
            const title = this.querySelector('h3').textContent;
            const description = this.querySelector('p').textContent;

            // Show notification instead of modal for demo
            window.notifications?.show(`Clicked on: ${title}`, 'info');
        });
    });

    // Add loading animation
    function showLoadingState() {
        portfolioContainer.innerHTML = '<div class="portfolio-loading">Chargement du portfolio...</div>';

        // Simulate loading
        setTimeout(() => {
            loadPortfolioItems();
        }, 1000);
    }

    function loadPortfolioItems() {
        // In a real app, this would load from an API
        console.log('Portfolio items loaded');
    }

    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    };

    const portfolioObserver = new IntersectionObserver(function(entries) {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    }, observerOptions);

    // Observe portfolio items for staggered animation
    portfolioItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(30px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        portfolioObserver.observe(item);
    });
});
""",
        "src/js/contact.js": """// Contact page specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');

    if (!contactForm) return;

    // Initialize form validator
    const validator = new FormValidator(contactForm);

    // Add validation rules
    validator.addRule('name', (value) => value.trim().length >= 2, 'Le nom doit contenir au moins 2 caractères');
    validator.addRule('email', (value) => /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value), 'Veuillez entrer un email valide');
    validator.addRule('subject', (value) => value.trim().length >= 5, 'Le sujet doit contenir au moins 5 caractères');
    validator.addRule('message', (value) => value.trim().length >= 10, 'Le message doit contenir au moins 10 caractères');

    // Handle form submission
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();

        if (validator.validate()) {
            submitForm();
        }
    });

    function submitForm() {
        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        // Show loading state
        submitBtn.textContent = 'Envoi en cours...';
        submitBtn.disabled = true;

        // Simulate form submission
        setTimeout(() => {
            // Reset form
            contactForm.reset();

            // Reset button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;

            // Show success message
            window.notifications?.show('Message envoyé avec succès!', 'success');

        }, 2000);
    }

    // Auto-save form data to localStorage
    const formFields = contactForm.querySelectorAll('input, textarea');

    formFields.forEach(field => {
        // Load saved data
        const savedValue = localStorage.getItem(`contact_${field.name}`);
        if (savedValue) {
            field.value = savedValue;
        }

        // Save on input
        field.addEventListener('input', function() {
            localStorage.setItem(`contact_${this.name}`, this.value);
        });
    });

    // Clear saved data on successful submission
    contactForm.addEventListener('submit', function() {
        if (validator.validate()) {
            formFields.forEach(field => {
                localStorage.removeItem(`contact_${field.name}`);
            });
        }
    });

    // Character counter for textarea
    const messageField = contactForm.querySelector('#message');
    if (messageField) {
        const counter = document.createElement('div');
        counter.className = 'character-counter';
        counter.style.cssText = 'text-align: right; margin-top: 5px; font-size: 0.9rem; color: #777;';
        messageField.parentNode.appendChild(counter);

        function updateCounter() {
            const length = messageField.value.length;
            const maxLength = messageField.getAttribute('maxlength') || 500;
            counter.textContent = `${length}/${maxLength} caractères`;

            if (length > maxLength * 0.9) {
                counter.style.color = '#e74c3c';
            } else {
                counter.style.color = '#777';
            }
        }

        messageField.addEventListener('input', updateCounter);
        updateCounter(); // Initial count
    }
});
""",
        # Documentation
        "docs/README.md": """# Documentation Frontend

## Structure du projet

### Répertoires
- `public/` - Pages HTML publiques
- `src/css/` - Feuilles de style
- `src/js/` - Scripts JavaScript
- `src/images/` - Images et assets
- `docs/` - Documentation

### Pages
- `index.html` - Page d'accueil
- `about.html` - Page à propos
- `portfolio.html` - Portfolio des projets
- `contact.html` - Formulaire de contact

### Styles CSS
- `main.css` - Styles principaux et variables CSS
- `components.css` - Styles des composants spécifiques
- `forms.css` - Styles des formulaires
- `portfolio.css` - Styles spécifiques au portfolio

### Scripts JavaScript
- `main.js` - JavaScript principal et navigation
- `components.js` - Composants réutilisables (Modal, Notifications, Validation)
- `portfolio.js` - Fonctionnalités du portfolio
- `contact.js` - Gestion du formulaire de contact

## Fonctionnalités

### Responsive Design
- Design adaptatif pour tous les écrans
- Navigation mobile avec menu hamburger
- Grilles CSS flexibles

### Interactivité
- Navigation fluide
- Filtrage du portfolio
- Validation de formulaire en temps réel
- Système de notifications
- Animations au scroll

### Accessibilité
- HTML sémantique
- Attributs ARIA appropriés
- Contraste des couleurs respecté
- Navigation au clavier

## Utilisation avec cli_workspace

Ce projet sert de workspace de test pour le cli_workspace.py. Exemples d'utilisation :

```bash
# Analyser la structure
python cli_workspace.py frontend_workspace "Analyse la structure du projet frontend"

# Modifier les styles
python cli_workspace.py frontend_workspace "Ajoute un thème sombre au CSS"

# Optimiser le code
python cli_workspace.py frontend_workspace "Optimise le JavaScript pour les performances"
```
""",
        "docs/STYLES.md": """# Guide des Styles CSS

## Variables CSS

Le projet utilise des variables CSS personnalisées définies dans `:root` :

```css
:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --accent-color: #e74c3c;
    --text-color: #333;
    --text-light: #777;
    --bg-color: #fff;
    --bg-light: #f8f9fa;
    --border-color: #ddd;
    --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    --border-radius: 8px;
    --transition: all 0.3s ease;
}
```

## Grille CSS

Utilisation de CSS Grid pour les layouts :

- `.features-grid` - Grille responsive pour les fonctionnalités
- `.portfolio-grid` - Grille du portfolio
- `.content-grid` - Grille de contenu 2 colonnes
- `.contact-grid` - Grille du formulaire de contact

## Classes utilitaires

- `.text-center`, `.text-left`, `.text-right` - Alignement du texte
- `.mt-1`, `.mt-2`, `.mb-1`, `.mb-2` - Marges
- `.p-1`, `.p-2` - Padding

## Composants

### Boutons
- `.btn` - Style de base
- `.btn-primary` - Bouton principal
- `.btn-secondary` - Bouton secondaire

### Cartes
- `.feature-card` - Carte de fonctionnalité
- `.portfolio-item` - Élément du portfolio

### Navigation
- `.navbar` - Barre de navigation
- `.nav-link` - Liens de navigation
- `.mobile-toggle` - Toggle mobile

## Animations

- Transitions CSS pour les interactions
- Animations au scroll avec Intersection Observer
- Effets de hover sur les cartes et boutons
""",
        # Test files
        "tests/test-plan.md": """# Plan de Tests Frontend

## Tests manuels

### Navigation
- [ ] Vérifier la navigation entre les pages
- [ ] Tester le menu mobile sur petits écrans
- [ ] Valider les liens actifs

### Responsive Design
- [ ] Tester sur mobile (320px-768px)
- [ ] Tester sur tablette (768px-1024px)
- [ ] Tester sur desktop (1024px+)

### Formulaire de Contact
- [ ] Validation des champs requis
- [ ] Validation format email
- [ ] Messages d'erreur appropriés
- [ ] Soumission réussie

### Portfolio
- [ ] Filtrage par catégorie
- [ ] Animations des éléments
- [ ] Responsivité de la grille

### Performance
- [ ] Temps de chargement < 3s
- [ ] Images optimisées
- [ ] CSS/JS minifiés en production

## Tests automatisés

```javascript
// Exemple de tests avec Jest
describe('Navigation', () => {
  test('should highlight active page', () => {
    // Test logic here
  });
});

describe('Portfolio Filter', () => {
  test('should filter items by category', () => {
    // Test logic here
  });
});
```

## Checklist Accessibilité

- [ ] Contraste des couleurs conforme WCAG
- [ ] Navigation au clavier possible
- [ ] Attributs alt sur les images
- [ ] Titres hiérarchiques corrects
- [ ] Labels appropriés sur les formulaires
""",
        # GitHub workflow
        ".github/workflows/frontend-ci.yml": """name: Frontend CI

on:
  push:
    branches: [ main ]
    paths: ['frontend_workspace/**']
  pull_request:
    branches: [ main ]
    paths: ['frontend_workspace/**']

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Validate HTML
      run: |
        npm install -g html-validate
        html-validate frontend_workspace/public/*.html

    - name: Lint CSS
      run: |
        npm install -g stylelint stylelint-config-standard
        stylelint "frontend_workspace/src/css/*.css"

    - name: Lint JavaScript
      run: |
        npm install -g eslint
        eslint frontend_workspace/src/js/*.js

    - name: Test with Lighthouse
      run: |
        npm install -g @lhci/cli
        # Add Lighthouse CI configuration
""",
    }

    # Write all files
    for file_path, content in files.items():
        full_path = base_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Make shell scripts executable
        if file_path.endswith(".sh"):
            os.chmod(full_path, 0o755)

    print(f"✅ Created frontend workspace in '{base_dir}' with {len(files)} files")
    print(f"📁 Directory structure: {', '.join(directories[:5])}...")
    print("🌐 Open public/index.html in your browser to view the site")


if __name__ == "__main__":
    create_frontend_workspace()

#!/usr/bin/env python3
"""
Worker script that runs inside the Docker container
Clones the repo, analyzes code quality issues, and generates recommendations using Ollama
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import git
from ollama import Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    def __init__(self):
        self.repo_url = os.getenv('REPO_URL')
        self.branch = os.getenv('BRANCH', 'main')
        self.job_id = os.getenv('JOB_ID')
        self.code_report = json.loads(os.getenv('CODE_REPORT', '{}'))
        self.workspace = Path('/workspace')
        self.repo_name = self.repo_url.split('/')[-1].replace('.git', '')
        self.repo_path = self.workspace / self.repo_name
        
        # Ollama configuration
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-coder:latest')
        self.ollama_client = Client(host=self.ollama_host)
        
    def clone_repository(self):
        """Clone the repository into the workspace"""
        try:
            logger.info(f"📥 Cloning repository: {self.repo_url}")
            
            # Clone with GitPython
            repo = git.Repo.clone_from(
                self.repo_url, 
                str(self.repo_path),
                branch=self.branch,
                depth=1  # Shallow clone for efficiency
            )
            
            logger.info(f"✅ Repository cloned to {self.repo_path}")
            return repo
            
        except Exception as e:
            logger.error(f"❌ Repository cloning failed: {e}")
            raise
    
    def read_relevant_files(self):
        """Read files mentioned in the code report"""
        file_contents = {}
        issues = self.code_report.get('issues', [])
        
        # Extract unique file paths from issues
        file_paths = set()
        for issue in issues:
            if 'file' in issue:
                file_paths.add(issue['file'])
        
        logger.info(f"📖 Reading {len(file_paths)} files from issues")
        
        for file_path in file_paths:
            try:
                full_path = self.repo_path / file_path
                if full_path.exists() and full_path.is_file():
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit file size to avoid overwhelming the model
                        if len(content) > 50000:
                            content = content[:50000] + "\n... (truncated)"
                        file_contents[file_path] = content
                        logger.info(f"✅ Read file: {file_path}")
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
            except Exception as e:
                logger.error(f"❌ Error reading {file_path}: {e}")
        
        return file_contents
    
    def analyze_code_structure(self):
        """Analyze the overall code structure"""
        structure_info = {
            "total_files": 0,
            "file_types": {},
            "directories": []
        }
        
        try:
            for root, dirs, files in os.walk(self.repo_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                rel_path = os.path.relpath(root, self.repo_path)
                if rel_path != '.':
                    structure_info["directories"].append(rel_path)
                
                for file in files:
                    if not file.startswith('.'):
                        structure_info["total_files"] += 1
                        ext = Path(file).suffix
                        if ext:
                            structure_info["file_types"][ext] = structure_info["file_types"].get(ext, 0) + 1
            
            logger.info(f"📊 Found {structure_info['total_files']} files in {len(structure_info['directories'])} directories")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing structure: {e}")
        
        return structure_info
    
    def build_analysis_prompt(self, file_contents, structure_info):
        """Build a comprehensive prompt for Ollama"""
        issues = self.code_report.get('issues', [])
        metrics = self.code_report.get('metrics', {})
        
        # Categorize issues
        critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
        major_issues = [i for i in issues if i.get('severity') == 'MAJOR']
        minor_issues = [i for i in issues if i.get('severity') == 'MINOR']
        security_issues = [i for i in issues if i.get('type') == 'VULNERABILITY']
        
        prompt = f"""Vous êtes un expert en analyse de code et sécurité logicielle. Analysez ce rapport de qualité de code et fournissez des recommandations détaillées pour améliorer le projet.

# INFORMATIONS DU PROJET

Repository: {self.repo_name}
Branche: {self.branch}

## Structure du projet:
- Nombre total de fichiers: {structure_info['total_files']}
- Types de fichiers: {json.dumps(structure_info['file_types'], indent=2)}
- Répertoires principaux: {', '.join(structure_info['directories'][:10])}

## RAPPORT DE QUALITÉ

### Résumé des problèmes:
- Issues critiques: {len(critical_issues)}
- Issues majeures: {len(major_issues)}
- Issues mineures: {len(minor_issues)}
- Vulnérabilités de sécurité: {len(security_issues)}
- Total des issues: {len(issues)}

### Métriques de qualité:
{json.dumps(metrics, indent=2)}

### Détail des issues principales:
"""
        
        # Add top 20 issues with context
        for i, issue in enumerate(issues[:20], 1):
            prompt += f"\n#### Issue {i}:\n"
            prompt += f"- **Fichier**: {issue.get('file', 'N/A')}\n"
            prompt += f"- **Ligne**: {issue.get('line', 'N/A')}\n"
            prompt += f"- **Type**: {issue.get('type', 'N/A')}\n"
            prompt += f"- **Sévérité**: {issue.get('severity', 'N/A')}\n"
            prompt += f"- **Message**: {issue.get('message', 'N/A')}\n"
            prompt += f"- **Règle**: {issue.get('key', 'N/A')}\n"
        
        # Add file contents for context
        if file_contents:
            prompt += "\n\n## CODE SOURCE DES FICHIERS AFFECTÉS\n\n"
            for file_path, content in list(file_contents.items())[:5]:  # Limit to 5 files
                prompt += f"### Fichier: {file_path}\n```\n{content[:2000]}\n```\n\n"
        
        prompt += """
# INSTRUCTIONS POUR L'ANALYSE

Fournissez une analyse complète et des recommandations en suivant cette structure:

## 1. ANALYSE GLOBALE
- Évaluation générale de la qualité du code
- Principaux points forts et faiblesses identifiés
- Risques majeurs pour le projet

## 2. PROBLÈMES CRITIQUES À RÉSOUDRE EN PRIORITÉ
Pour chaque problème critique:
- Description du problème
- Impact potentiel
- Solution recommandée avec exemple de code si pertinent
- Estimation de l'effort requis

## 3. VULNÉRABILITÉS DE SÉCURITÉ
Pour chaque vulnérabilité:
- Nature de la vulnérabilité
- Vecteur d'attaque potentiel
- Correction recommandée
- Bonnes pratiques à adopter

## 4. AMÉLIORATIONS DE LA QUALITÉ DU CODE
- Problèmes de maintenabilité
- Code smells à corriger
- Suggestions de refactoring
- Patterns à implémenter

## 5. OPTIMISATIONS DE PERFORMANCE
- Goulots d'étranglement potentiels
- Optimisations recommandées
- Impact attendu

## 6. PLAN D'ACTION RECOMMANDÉ
- Ordre de priorité des corrections
- Estimation du temps nécessaire
- Quick wins vs changements structurels
- Recommandations pour la prévention future

Utilisez un langage clair et professionnel. Soyez spécifique dans vos recommandations et fournissez des exemples concrets quand c'est pertinent.
"""
        
        return prompt
    
    def analyze_with_ollama(self, prompt):
        """Send the analysis prompt to Ollama and get recommendations"""
        try:
            logger.info(f"🤖 Sending analysis to Ollama ({self.ollama_model})...")
            
            response = self.ollama_client.chat(
                model=self.ollama_model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            recommendations = response['message']['content']
            logger.info("✅ Received recommendations from Ollama")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Ollama analysis failed: {e}")
            raise
    
    def save_recommendations(self, recommendations):
        """Save the recommendations to a markdown file"""
        try:
            recommendations_file = Path(f'/app/logs/recommendations_{self.job_id}.md')
            
            # Add header with metadata
            header = f"""# 🔍 Code Quality Analysis Report

**Repository**: {self.repo_url}  
**Branch**: {self.branch}  
**Job ID**: {self.job_id}  
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Model**: {self.ollama_model}

---

"""
            
            with open(recommendations_file, 'w', encoding='utf-8') as f:
                f.write(header + recommendations)
            
            logger.info(f"✅ Recommendations saved to {recommendations_file}")
            
            # Also save a summary
            summary = {
                "job_id": self.job_id,
                "repo_url": self.repo_url,
                "branch": self.branch,
                "analysis_date": datetime.now().isoformat(),
                "model_used": self.ollama_model,
                "total_issues": len(self.code_report.get('issues', [])),
                "recommendations_file": str(recommendations_file)
            }
            
            summary_file = Path(f'/app/logs/summary_{self.job_id}.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            return recommendations_file
            
        except Exception as e:
            logger.error(f"❌ Failed to save recommendations: {e}")
            raise
    
    def run(self):
        """Main entry point of the analyzer"""
        try:
            logger.info(f"🚀 Starting code analysis job {self.job_id}")
            logger.info(f"📍 Repository: {self.repo_url}")
            logger.info(f"🌿 Branch: {self.branch}")
            logger.info(f"🤖 Ollama host: {self.ollama_host}")
            
            # 1. Clone repository
            self.clone_repository()
            
            # 2. Read relevant files
            file_contents = self.read_relevant_files()
            
            # 3. Analyze code structure
            structure_info = self.analyze_code_structure()
            
            # 4. Build analysis prompt
            prompt = self.build_analysis_prompt(file_contents, structure_info)
            
            # 5. Get recommendations from Ollama
            recommendations = self.analyze_with_ollama(prompt)
            
            # 6. Save recommendations
            recommendations_file = self.save_recommendations(recommendations)
            
            logger.info(f"🎉 Analysis completed successfully!")
            logger.info(f"📄 Recommendations available at: {recommendations_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"💥 Job failed: {e}")
            raise


if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    analyzer.run()
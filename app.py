from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # Salli pyynnöt WordPressiltä

class BeeSwarmDecision:
    """Mehiläisparvi-päätöksentekoalgoritmi"""
    
    def __init__(self, quorum_threshold=3):
        self.ideas = {}
        self.comments = []
        self.quorum_threshold = quorum_threshold
        
    def add_idea(self, idea_id, title):
        """Lisää uusi idea"""
        self.ideas[idea_id] = {
            'id': idea_id,
            'title': title,
            'strength': 0,
            'engaged_users': set(),
            'comment_weights': []
        }
        
    def classify_comment(self, text):
    """Luokittele kommentti ja anna paino"""
    text_lower = text.lower()
    
    # Haaste - vähentää vahvuutta (KORJATTU)
    challenge_words = [
        'en voi', 'ei toimi', 'ei sovi', 'ei ole', 'ei', 
        'allergia', 'ongelma', 'ei pysty', 'gluteeni',
        'liian', 'huono', 'ei käy', 'ei gluteenitonta', 'en voi', 'en pysty'
    ]
    challenge_emojis = ['🚫', '❌', '🙅', '⛔']
    
    if any(word in text_lower for word in challenge_words) or any(emoji in text for emoji in challenge_emojis):
        return {'type': 'haaste', 'weight': -2}
    
    # Kehitys - lisää vahvuutta
    develop_words = ['voisiko', 'entä jos', 'kysyä', 'ehkä', 'voisi']
    if any(word in text_lower for word in develop_words):
        return {'type': 'kehitys', 'weight': 3}
    
    # Yhdistys - vahva lisäys
    combine_words = ['yhdistetään', 'plus', 'samalla']
    if any(word in text_lower for word in combine_words):
        return {'type': 'yhdistys', 'weight': 4}
    
    # Tuki - perus lisäys
    return {'type': 'tuki', 'weight': 2}
    
    def add_comment(self, idea_id, user, text):
        """Lisää kommentti idealle"""
        if idea_id not in self.ideas:
            return None
            
        classification = self.classify_comment(text)
        
        comment = {
            'idea_id': idea_id,
            'user': user,
            'text': text,
            'type': classification['type'],
            'weight': classification['weight']
        }
        
        self.comments.append(comment)
        
        # Päivitä idean vahvuus
        idea = self.ideas[idea_id]
        idea['comment_weights'].append(classification['weight'])
        idea['strength'] = sum(idea['comment_weights'])
        idea['engaged_users'].add(user)
        
        return comment
    
    def check_quorum(self, idea_id):
        """Tarkista saavuttiko idea quorumin"""
        if idea_id not in self.ideas:
            return False
            
        idea = self.ideas[idea_id]
        return len(idea['engaged_users']) >= self.quorum_threshold
    
    def get_results(self):
        """Palauta tulokset järjestettynä vahvuuden mukaan"""
        results = []
        
        for idea_id, idea in self.ideas.items():
            results.append({
                'id': idea['id'],
                'title': idea['title'],
                'strength': idea['strength'],
                'engaged_count': len(idea['engaged_users']),
                'quorum_reached': len(idea['engaged_users']) >= self.quorum_threshold,
                'comments': [c for c in self.comments if c['idea_id'] == idea_id]
            })
        
        # Järjestä vahvuuden mukaan
        results.sort(key=lambda x: x['strength'], reverse=True)
        
        return results

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Mehiläisparvi API toimii!',
        'endpoints': {
            '/api/process': 'POST - Käsittele päätöstä'
        }
    })

@app.route('/api/process', methods=['POST'])
def process():
    """Käsittele mehiläisparvi-päätös"""
    try:
        data = request.get_json()
        
        # Alusta algoritmi
        quorum = data.get('quorum', 3)
        swarm = BeeSwarmDecision(quorum_threshold=quorum)
        
        # Lisää ideat
        for idea in data.get('ideas', []):
            swarm.add_idea(idea['id'], idea['title'])
        
        # Lisää kommentit
        for comment in data.get('comments', []):
            swarm.add_comment(
                comment['idea_id'],
                comment['user'],
                comment['text']
            )
        
        # Palauta tulokset
        results = swarm.get_results()
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
# ⭐ health-check
@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/process', methods=['POST'])
def process():
    # ... (kaikki aiempi koodi pysyy samana)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

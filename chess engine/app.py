"""
Flask API for chess game
"""
from flask import Flask, jsonify, request
from chess_game import ChessGame
from chess_board import Color
from engine import ChessEngine
import json

app = Flask(__name__)
game = ChessGame()
engine = ChessEngine(depth=2)

@app.route('/api/game/status', methods=['GET'])
def get_game_status():
    """Get current game status"""
    status = game.get_game_status()
    return jsonify(status)

@app.route('/api/game/board', methods=['GET'])
def get_board():
    """Get current board state"""
    board = game.get_board_as_list()
    return jsonify({'board': board})

@app.route('/api/game/move', methods=['POST'])
def make_move():
    """Make a move"""
    data = request.json
    from_row = data.get('from_row')
    from_col = data.get('from_col')
    to_row = data.get('to_row')
    to_col = data.get('to_col')
    
    if not all(x is not None for x in [from_row, from_col, to_row, to_col]):
        return jsonify({'success': False, 'error': 'Missing coordinates'}), 400
    
    success = game.make_move(from_row, from_col, to_row, to_col)
    
    if success:
        return jsonify({
            'success': True,
            'game_status': game.get_game_status()
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid move'}), 400

@app.route('/api/game/moves', methods=['POST'])
def get_moves():
    """Get available moves for a piece"""
    data = request.json
    row = data.get('row')
    col = data.get('col')
    
    if row is None or col is None:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    moves = game.board.get_legal_moves(row, col, game.en_passant_target)
    legal_moves = []
    
    # Filter moves that don't leave king in check
    for to_row, to_col in moves:
        if game._is_legal_move(row, col, to_row, to_col, game.current_player):
            piece = game.board.get_piece(row, col)
            target = game.board.get_piece(to_row, to_col)
            is_en_passant = False
            if piece and piece.type.name == 'PAWN' and target is None and game.en_passant_target == (to_row, to_col):
                is_en_passant = True
            legal_moves.append({'row': to_row, 'col': to_col, 'capture': bool(target) or is_en_passant})
    
    return jsonify({'moves': legal_moves})

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Reset the game"""
    global game
    game = ChessGame()
    return jsonify({'success': True, 'game_status': game.get_game_status()})

@app.route('/api/game/engine-move', methods=['POST'])
def engine_move():
    """Let the built-in engine play the current side."""
    if game.game_over:
        return jsonify({'success': False, 'error': 'Game is already over'}), 400

    move = engine.choose_move(game)
    if move is None:
        return jsonify({'success': False, 'error': 'No legal moves available'}), 400

    success = game.make_move(*move)
    if not success:
        return jsonify({'success': False, 'error': 'Engine move was invalid'}), 400

    return jsonify({
        'success': True,
        'move': {
            'from_row': move[0],
            'from_col': move[1],
            'to_row': move[2],
            'to_col': move[3]
        },
        'game_status': game.get_game_status()
    })

@app.route('/api/game/validate', methods=['POST'])
def validate_move():
    """Validate if a move is legal"""
    data = request.json
    from_row = data.get('from_row')
    from_col = data.get('from_col')
    to_row = data.get('to_row')
    to_col = data.get('to_col')
    
    is_valid = game.is_move_valid(from_row, from_col, to_row, to_col)
    return jsonify({'valid': is_valid})

@app.route('/')
def index():
    """Serve the main page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chess</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div id="app">
            <h1>Chess Game</h1>
            <div id="game-container">
                <div id="board"></div>
                <div id="status">
                    <p>Current Player: <span id="current-player">White</span></p>
                    <p>Status: <span id="game-status">In Progress</span></p>
                    <button onclick="resetGame()">New Game</button>
                </div>
            </div>
            <div id="info">
                <h3>How to Play:</h3>
                <p>Click a piece to select it, then click a square to move it.</p>
                <p>White plays at the bottom, Black at the top.</p>
            </div>
        </div>
        <script src="/static/script.js"></script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)

import requests
import numpy as np
import random
import time

from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import List
from pyngrok import ngrok  # Import Ngrok

ROWS = 6
COLS = 7
AI = 1  # player 1
PLAYER = 2  # player2
EMPTY = 0
MAX_DEPTH = 5  # Độ sâu tìm kiếm

def create_board():
    return np.zeros((ROWS, COLS), dtype=int)

# kiểm tra 1 cột có valid
def is_valid_move(board, col):
    return col >= 0 and col < COLS and board[0][col] == EMPTY

# lấy tất cả các cột valid
def get_valid_moves(board):
    return [col for col in range(COLS) if is_valid_move(board, col)]

# gán giá trị cho ô trong bảng
def drop_piece(board, row, col, player):
    board[row][col] = player

# in bảng
def print_board(board):
    print(np.where(board == EMPTY, 0, np.where(board == AI, AI, PLAYER)))


# kiểm tra nước đi đã thắng chưa
def is_winning_move(board, player):
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False

def is_draw(board):
    return all(board[0][col] != EMPTY for col in range(COLS))

# lấy vị trí row thấp nhất trong columns
def get_row(board, col):
    row = ROWS - 1
    while(board[row][col] != EMPTY):
        row -= 1
    return row


def output(old_board, new_board, str_state):
    if all(all(cell == 0 for cell in row) for row in new_board):
        old_board = [[0] * 7 for _ in range(6)]
        str_state = ""

    for i in range(len(old_board)):
        for j in range(len(old_board[0])):
            if old_board[i][j] != new_board[i][j]:
                str_state += str(j+1)

    try:
        url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        # print(url, data)
        idx = 1
        max_score = -100
        for move in data:
            print(move)
            if move["score"] > max_score:
                max_score = move["score"]
                idx = move["move"]
        return (int(move["move"])-1, str_state)
    except:
        return 0, str_state

def play_game(curent_player):
    # khởi tạo 2 board và str_state ban đầu
    old_board = create_board() #board sau lượt AI
    new_board = np.copy(old_board) # board sau lượt player
    str_state = ""
    # người bắt đầu
    player = curent_player
    print_board(old_board)

    while True:
        if is_draw(old_board):
            print("Draw")
            break

        if(player == PLAYER):
            choose = int(input(f"Player {player} choose: "))
            # choose =
            while not is_valid_move(old_board, choose):
                choose = int(input("Invalid! Repeat choose: "))
            row = get_row(old_board, choose)
            new_board = np.copy(old_board)
            new_board[row][choose] = player
            print(new_board)
            if is_winning_move(new_board, player):
                print("Player", player, "win!")
                break
            player = PLAYER if player == AI else AI
        else:
            # choose, score = minimax(board, player, MAX_DEPTH, -np.inf, np.inf, True)
            (choose, str_state) = output(old_board, new_board, str_state)
            str_state += str(choose + 1)
            print((f"Player {player} choose: "), choose)
            row = get_row(new_board, choose)
            old_board = np.copy(new_board)
            old_board[row][choose] = player
            print(old_board)
            if(is_winning_move(old_board, player)):
                print("Player", player, "win!")
                break
            player = PLAYER if player == AI else AI

# if __name__ == "__main__":
#     play_game(PLAYER)


app = FastAPI()

class GameState(BaseModel):
    board: List[List[int]]
    current_player: int
    valid_moves: List[int]

class AIResponse(BaseModel):
    move: int

MAX_DEPTH = 4
old_board = [[0] * 7 for _ in range(6)]
str_state = ""

def minimax(board, depth, alpha, beta, maximizing_player, current_player):
    return random.choice([move for move in range(len(board[0])) if board[0][move] == 0])

@app.get("/api/test")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

@app.post("/api/connect4-move")
async def make_move(game_state: GameState) -> AIResponse:
    print("")
    try:
        start_time = time.time()
        global old_board, str_state
        if not game_state.valid_moves:
            raise ValueError("Không có nước đi hợp lệ")
        new_board = game_state.board
        print("New")
        print(new_board)

        selected_move, str_state = output(old_board, new_board, str_state)
        str_state += str(selected_move + 1)
        print(str_state)
        old_board = new_board
        row = get_row(old_board, selected_move)
        old_board[row][selected_move] = game_state.current_player
        if(is_winning_move(old_board, game_state.current_player)):
            print("You win")
            old_board = [[0] * 7 for _ in range(6)]
            str_state = ""

        # break
        print(old_board)
        period_time =  time.time() - start_time
        print("time = ", period_time)
        # return AIResponse(move=selected_move)
        return AIResponse(move=game_state.valid_moves[0])
    except Exception as e:
        if game_state.valid_moves:
            return AIResponse(move=game_state.valid_moves[0])
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    port = 8080
    public_url = ngrok.connect(port).public_url  # Kết nối ngrok
    print(f"🔥 Public URL: {public_url}")  # Hiển thị link API

    # Chạy FastAPI với Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
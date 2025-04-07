import pygame
import chess
import time
import threading

pygame.init()
board_size = 640
extra_panel_width = 160
width, height = board_size + 2 * extra_panel_width, board_size
square_size = board_size // 8
colors = [(240, 217, 181), (181, 136, 99)]
promotion_choises = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
piece_images = {}
promotion_image_keys = {chess.QUEEN: "wq", chess.ROOK: "wr", chess.BISHOP: "wb", chess.KNIGHT: "wn"}
promotion_active = False
white_ai_thinking = False
ai_thinking = False
selected_promotion_piece = chess.QUEEN
promotion_square = None
pending_move = None
player_wins = 0
computer_wins = 0
game_over_text = ""
score_updated = False
black_depth = 2
white_depth = 2
black_eval_choice = 1
white_eval_choice = 1
difficulty_selected = True
show_restart = False
restart_button = None
is_white_ai_enabled = True
font = pygame.font.SysFont("Arial", 24)
large_font = pygame.font.SysFont("Arial", 56)

def load_piece_images():
    pieces = ["r", "n", "b", "q", "k", "p"]
    for color in ["w", "b"]:
        for piece in pieces:
            image = pygame.image.load(f"./imgs-128px/{color}{piece}.png")
            image = pygame.transform.scale(image, (square_size, square_size))
            piece_images[color + piece] = image

def draw_board(screen):
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            rect = pygame.Rect(extra_panel_width + col * square_size, row * square_size, square_size, square_size)
            pygame.draw.rect(screen, color, rect)

def draw_pieces(screen, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row, col = divmod(square, 8)
            key = f"{'w' if piece.color == chess.WHITE else 'b'}{piece.symbol().lower()}"
            screen.blit(piece_images[key], (extra_panel_width + col * square_size, (7 - row) * square_size))

def draw_legal_moves(screen, board, selected_square):
    if selected_square is not None:
        for move in board.legal_moves:
            if move.from_square == selected_square:
                row, col = divmod(move.to_square, 8)
                square_rect = pygame.Rect(extra_panel_width + col * square_size, (7 - row) * square_size, square_size, square_size)
                if board.piece_at(move.to_square) is not None:
                    highlight_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                    highlight_surface.fill((255, 0, 0))
                    screen.blit(highlight_surface, square_rect.topleft)
                else:
                    highlight_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                    highlight_surface.fill((0, 255, 0, 128))
                    screen.blit(highlight_surface, square_rect.topleft)


def evaluate_board_1(board):
    piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value 
            else:
                score -= value 
    return score

def evaluate_board_2(board):
    piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
    score = 0
    if board.is_checkmate():
        return 2000000
    if board.is_check():
        score += 50 if board.turn == chess.WHITE else -50
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                score += value 
            else:
                score -= value 
    return score

def evaluate_board_3(board):
    piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}
    pawn_table = [
         0,  0,  0,   0,   0,  0,  0,  0,
         5, 10, 10, -20, -20, 10, 10,  5,
         5, -5,-10,   0,   0,-10, -5,  5,
         0,  0,  0,  20,  20,  0,  0,  0,
         5,  5, 10,  25,  25, 10,  5,  5,
        10, 10, 20,  30,  30, 20, 10, 10,
        50, 50, 50,  50,  50, 50, 50, 50,
         0,  0,  0,   0,   0,  0,  0,  0
    ]
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    bishop_table = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    rook_table = [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         0,  0,  0,  5,  5,  0,  0,  0
    ]
    queen_table = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    king_table = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20
    ]
    piece_square_tables = {chess.PAWN: pawn_table, chess.KNIGHT: knight_table, chess.BISHOP: bishop_table, chess.ROOK: rook_table, chess.QUEEN: queen_table, chess.KING: king_table }

    score = 0
    if board.is_checkmate():
        return 2000000
    if board.is_check():
        score += 50 if board.turn == chess.WHITE else -50

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            table = piece_square_tables[piece.piece_type]
            if piece.color == chess.WHITE:
                pos_value = table[square]
            else:
                pos_value = table[chess.square_mirror(square)]
            if piece.color == chess.WHITE:
                score += value + pos_value
            else:
                score -= value + pos_value
    return score

def minimax(board, depth, alpha, beta, maximizing):
    if board.is_checkmate():
        return -2000000 if maximizing else 2000000
    if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition():
        return 0
    if depth == 0:
        if not white_ai_thinking:
            if black_eval_choice == 1 :
                return evaluate_board_1(board)
            if black_eval_choice == 2 :
                return evaluate_board_2(board)
            if black_eval_choice == 3 :
                return evaluate_board_3(board)
        else:
            if white_eval_choice == 1 :
                return -evaluate_board_1(board)
            if white_eval_choice == 2 :
                return -evaluate_board_2(board)
            if white_eval_choice == 3 :
                return -evaluate_board_3(board)
            
    legal_moves = list(board.legal_moves)
    if maximizing:
        max_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            if max_eval >= beta:
                return max_eval
            alpha = max(alpha, eval_score)
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            if min_eval <= alpha:
                return min_eval
            beta = min(beta, eval_score)
        return min_eval

def get_best_move(board, depth):
    best_move = None
    min_eval = float('inf')
    alpha = float('-inf')
    beta = float('inf')
    legal_moves = list(board.legal_moves)
    for move in legal_moves:
        board.push(move)
        if board.is_checkmate():
            board.pop()
            return move
        eval_score = minimax(board, depth - 1, alpha, beta, True)
        board.pop()
        if eval_score < min_eval:
            min_eval = eval_score
            best_move = move
    return best_move

def check_pawn_promotion_ai():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            if piece.color == chess.BLACK and square // 8 == 0:
                board.push(chess.Move(square, square, promotion=chess.QUEEN))

def white_ai_move():
    global board, ai_thinking, white_ai_thinking, is_white_ai_enabled
    if board.is_game_over():
        white_ai_thinking = False
        ai_thinking = False
        is_white_ai_enabled = False
        return
    best_move = get_best_move(board, white_depth)
    if best_move:
        board.push(best_move)
        check_pawn_promotion_ai()
    ai_thinking = False
    white_ai_thinking = False
    time.sleep(0.35)
    ai_move()

def ai_move():
    global board, ai_thinking, white_ai_thinking, is_white_ai_enabled
    if not white_ai_thinking:
        ai_thinking = True
        if board.is_game_over():
            ai_thinking = False
            is_white_ai_enabled = False
            return
        best_move = get_best_move(board, black_depth)
        if best_move:
            time.sleep(0.35)
            board.push(best_move)
            check_pawn_promotion_ai()
        ai_thinking = False
        is_white_ai_enabled = True

def show_promotion_options(square):
    global promotion_active, promotion_square, selected_promotion_piece
    promotion_active = True
    promotion_square = square
    selected_promotion_piece = chess.QUEEN

def draw_promotion_box(screen):
    if promotion_active:
        box_x, box_y = extra_panel_width + 10, 270
        box_width, box_height = board_size - 20, 100
        promotion_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        promotion_box.fill((0, 0, 0, 180))
        num_options = len(promotion_choises)
        image_size = 60
        spacing = (box_width - num_options * image_size) // (num_options + 1)

        for i, piece_type in enumerate(promotion_choises):
            key = promotion_image_keys[piece_type]
            option_image = pygame.transform.scale(piece_images[key], (image_size, image_size))
            option_x = spacing + i * (image_size + spacing)
            option_y = (box_height - image_size) // 2
            promotion_box.blit(option_image, (option_x, option_y))
        screen.blit(promotion_box, (box_x, box_y))

def handle_promotion_choice(mouse_pos):
    global promotion_active, selected_promotion_piece, pending_move, ai_thinking
    if promotion_active and pending_move is not None:
        box_x, box_y = extra_panel_width + 10, 270
        box_width, box_height = board_size - 20, 100
        num_options = len(promotion_choises)
        image_size = 60
        spacing = (box_width - num_options * image_size) // (num_options + 1)
        x, y = mouse_pos

        if box_x <= x <= box_x + box_width and box_y <= y <= box_y + box_height:
            rel_x = x - box_x
            for i in range(num_options):
                option_x = spacing + i * (image_size + spacing)
                if option_x <= rel_x <= option_x + image_size:
                    selected_promotion_piece = promotion_choises[i]
                    break
            promotion_move = chess.Move(pending_move.from_square, pending_move.to_square, promotion=selected_promotion_piece)
            
            if promotion_move in board.legal_moves:
                board.push(promotion_move)
            pending_move = None
            promotion_active = False
            if not board.is_game_over():
                draw_board(screen)
                draw_legal_moves(screen, board, selected_square)
                draw_pieces(screen, board)
                draw_promotion_box(screen)
                pygame.display.flip()
                threading.Thread(target=ai_move, daemon=True).start()

def draw_center_text(surface, text, pos, color=(255,255,255)):
    label = large_font.render(text, True, color)
    rect = label.get_rect(center=pos)
    surface.blit(label, rect)

def draw_left_panel(screen):
    panel_rect = pygame.Rect(0, 0, extra_panel_width, height)
    pygame.draw.rect(screen, (200, 200, 200), panel_rect)
    title = font.render("Black AI", True, (0,0,0))
    screen.blit(title, (10, 10))
    depth_title = font.render("Depth", True, (0,0,0))
    screen.blit(depth_title, (10, 50))
    btn_width, btn_height = 120, 40
    gap = 10
    btn_y = 80
    black_depth_buttons = {}
    depths = {"Easy":2, "Medium":3, "Hard":4}

    for label_text, d in depths.items():
        btn_rect = pygame.Rect(10, btn_y, btn_width, btn_height)
        color_btn = (0, 200, 0) if black_depth == d else (100, 100, 100)
        pygame.draw.rect(screen, color_btn, btn_rect)
        txt = font.render(label_text, True, (255,255,255))
        screen.blit(txt, txt.get_rect(center=btn_rect.center))
        black_depth_buttons[label_text] = btn_rect
        btn_y += btn_height + gap

    eval_title = font.render("Eval", True, (0,0,0))
    screen.blit(eval_title, (10, btn_y + gap))
    btn_y += gap + 30
    black_eval_buttons = {}
    evals = {"E1":1, "E2":2, "E3":3}

    for label_text, val in evals.items():
        btn_rect = pygame.Rect(10, btn_y, btn_width, btn_height)
        color_btn = (0, 200, 0) if black_eval_choice == val else (100, 100, 100)
        pygame.draw.rect(screen, color_btn, btn_rect)
        txt = font.render(label_text, True, (255,255,255))
        screen.blit(txt, txt.get_rect(center=btn_rect.center))
        black_eval_buttons[label_text] = btn_rect
        btn_y += btn_height + gap

    turn_text = "White's turn" if board.turn == chess.WHITE and not ai_thinking else "Black's turn"
    turn_label = font.render(turn_text, True, (0,0,0))
    screen.blit(turn_label, (10, height - 110))
    score_label = font.render(f"Player: {player_wins}", True, (0,0,0))
    screen.blit(score_label, (10, height - 75))
    score_label2 = font.render(f"Computer: {computer_wins}", True, (0,0,0))
    screen.blit(score_label2, (10, height - 45))
    return black_depth_buttons, black_eval_buttons

def draw_right_panel(screen):
    panel_rect = pygame.Rect(extra_panel_width + board_size, 0, extra_panel_width, height)
    pygame.draw.rect(screen, (200, 200, 200), panel_rect)
    title = font.render("White AI", True, (0,0,0))
    screen.blit(title, (extra_panel_width + board_size + 10, 10))
    depth_title = font.render("Depth", True, (0,0,0))
    screen.blit(depth_title, (extra_panel_width + board_size + 10, 50))
    btn_width, btn_height = 120, 40
    gap = 10
    btn_y = 80
    white_depth_buttons = {}
    depths = {"Easy":2, "Medium":3, "Hard":4}

    for label_text, d in depths.items():
        btn_rect = pygame.Rect(extra_panel_width + board_size + 10, btn_y, btn_width, btn_height)
        color_btn = (0, 200, 0) if white_depth == d else (100, 100, 100)
        pygame.draw.rect(screen, color_btn, btn_rect)
        txt = font.render(label_text, True, (255,255,255))
        screen.blit(txt, txt.get_rect(center=btn_rect.center))
        white_depth_buttons[label_text] = btn_rect
        btn_y += btn_height + gap

    eval_title = font.render("Eval", True, (0,0,0))
    screen.blit(eval_title, (extra_panel_width + board_size + 10, btn_y + gap))
    btn_y += gap + 30
    white_eval_buttons = {}
    evals = {"E1":1, "E2":2, "E3":3}

    for label_text, val in evals.items():
        btn_rect = pygame.Rect(extra_panel_width + board_size + 10, btn_y, btn_width, btn_height)
        color_btn = (0, 200, 0) if white_eval_choice == val else (100, 100, 100)
        pygame.draw.rect(screen, color_btn, btn_rect)
        txt = font.render(label_text, True, (255,255,255))
        screen.blit(txt, txt.get_rect(center=btn_rect.center))
        white_eval_buttons[label_text] = btn_rect
        btn_y += btn_height + gap

    white_ai_button = pygame.Rect(extra_panel_width + board_size + 10, height - 120, 120, 40)
    pygame.draw.rect(screen, (50, 50, 200), white_ai_button)
    white_ai_text = font.render("White AI", True, (255,255,255))
    screen.blit(white_ai_text, white_ai_text.get_rect(center=white_ai_button.center))
    return white_depth_buttons, white_eval_buttons, white_ai_button

def draw_restart_button(screen):
    restart_button = pygame.Rect(extra_panel_width + board_size + 10, height - 60, 120, 40)
    pygame.draw.rect(screen, (150, 50, 50), restart_button)
    restart_text = font.render("Restart", True, (255,255,255))
    screen.blit(restart_text, restart_text.get_rect(center=restart_button.center))
    return restart_button
    
def restart_game():
    global board, selected_square, promotion_active, pending_move, score_updated, game_over_text, ai_thinking, is_white_ai_enabled, white_ai_thinking
    board = chess.Board()
    selected_square = None
    promotion_active = False
    pending_move = None
    score_updated = False
    game_over_text = ""
    ai_thinking = False
    white_ai_thinking = False
    is_white_ai_enabled = True

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Minimax Chess")
load_piece_images()
board = chess.Board()
running = True
selected_square = None
ai_thinking = False
clock = pygame.time.Clock()

while running:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if board.is_game_over() and event.type == pygame.MOUSEBUTTONDOWN:
            _ = draw_restart_button(screen)
            if restart_button.collidepoint(event.pos):
                restart_game()
            continue

        if event.type == pygame.MOUSEBUTTONDOWN:
            if promotion_active:
                handle_promotion_choice(event.pos)
                continue
            x, y = event.pos
            if x < extra_panel_width:
                b_depth_btns, b_eval_btns = draw_left_panel(screen)
                for label, btn in b_depth_btns.items():
                    if btn.collidepoint(event.pos):
                        if label == "Easy":
                            black_depth = 2
                        elif label == "Medium":
                            black_depth = 3
                        elif label == "Hard":
                            black_depth = 4
                for label, btn in b_eval_btns.items():
                    if btn.collidepoint(event.pos):
                        black_eval_choice = {"E1":1, "E2":2, "E3":3}[label]
                continue
            
            if x > extra_panel_width + board_size:
                w_depth_btns, w_eval_btns, white_ai_btn = draw_right_panel(screen)
                for label, btn in w_depth_btns.items():
                    if btn.collidepoint(event.pos):
                        if label == "Easy":
                            white_depth = 2
                        elif label == "Medium":
                            white_depth = 3
                        elif label == "Hard":
                            white_depth = 4
                for label, btn in w_eval_btns.items():
                    if btn.collidepoint(event.pos):
                        white_eval_choice = {"E1":1, "E2":2, "E3":3}[label]

                if white_ai_btn.collidepoint(event.pos) and is_white_ai_enabled and not board.is_game_over():
                    is_white_ai_enabled = False
                    draw_board(screen)
                    draw_legal_moves(screen, board, selected_square)
                    draw_pieces(screen, board)
                    draw_promotion_box(screen)
                    pygame.display.flip()
                    ai_thinking = True
                    white_ai_thinking = True
                    threading.Thread(target=white_ai_move, daemon=True).start()
                continue

            if extra_panel_width <= x <= extra_panel_width + board_size and y < board_size:
                board_x = x - extra_panel_width
                col, row = board_x // square_size, y // square_size
                square = chess.square(col, 7 - row)
                if selected_square is None:
                    if board.piece_at(square) and board.piece_at(square).color == chess.WHITE and not ai_thinking and not white_ai_thinking:
                        selected_square = square
                else:
                    move = chess.Move(selected_square, square)
                    if board.piece_at(selected_square).piece_type == chess.PAWN and square // 8 == 7:
                        for piece in ['q', 'b', 'r', 'n']:
                            for legal_move in list(board.legal_moves):
                                if str(move) + piece == str(legal_move):
                                    pending_move = move
                                    show_promotion_options(square)
                    if move in board.legal_moves:
                        board.push(move)
                        if not board.is_game_over():
                            draw_board(screen)
                            draw_legal_moves(screen, board, selected_square)
                            draw_pieces(screen, board)
                            draw_promotion_box(screen)
                            pygame.display.flip()
                            threading.Thread(target=ai_move, daemon=True).start()
                    selected_square = None

    if not white_ai_thinking or not ai_thinking:
        left_depth_btns, left_eval_btns = draw_left_panel(screen)
        right_depth_btns, right_eval_btns, white_ai_btn = draw_right_panel(screen)

    if board.is_game_over() and not score_updated and not white_ai_thinking and not ai_thinking:
        if board.is_checkmate():
            if board.turn == chess.WHITE:
                game_over_text = "Checkmate!\nBlack wins"
                computer_wins += 1
            else:
                game_over_text = "Checkmate!\nWhite wins"
                player_wins += 1
        elif board.is_stalemate():
            game_over_text = "Stalemate!"
        elif board.is_insufficient_material():
            game_over_text = "Draw: Insufficient material!"
        elif board.can_claim_threefold_repetition():
            game_over_text = "Draw: Threefold repetition!"
        elif board.can_claim_fifty_moves():
            game_over_text = "Draw: Fifty-move rule!"
        score_updated = True

    if not ai_thinking and not white_ai_thinking:
        draw_board(screen)
        draw_legal_moves(screen, board, selected_square)
        draw_pieces(screen, board)
        draw_promotion_box(screen)

    if board.is_game_over() and not ai_thinking and not white_ai_thinking:
        lines = game_over_text.split("\n")
        y_offset = board_size // 2 - len(lines) * 20
        for line in lines:
            game_over_surface = large_font.render(line, True, (200, 0, 0))
            screen.blit(game_over_surface, game_over_surface.get_rect(center=(extra_panel_width + board_size // 2, y_offset)))
            y_offset += 70
        restart_button = draw_restart_button(screen)

    pygame.display.flip()
pygame.quit()
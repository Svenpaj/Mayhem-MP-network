# import
from random import randint
import tkinter as tk
from tkinter import simpledialog, PhotoImage, Frame
from tkinter.ttk import Label
from PIL import Image, ImageTk
from network import connect, send
from tk_sleep import tk_sleep
from window_handler import create_window, start_window_loop
from style import set_style
import cv2

game_area_width = 1000
game_area_height = 460

# TKInter widgets
window = create_window(tk, 'Boss Mayhem Fight', 
    game_area_height + 160, game_area_width + 100)
set_style(window)
game_area  = Frame(window, bg='black', bd = 0,\
    height = game_area_height, width = game_area_width)
game_area.place(x=50, y=50)

background = ImageTk.PhotoImage(Image.open('images/bgdarkwood.png').resize((game_area_width, game_area_height), Image.Resampling.LANCZOS))
background_lbl = tk.Label(game_area, image=background)
background_lbl.place(relx=0.5, rely=0.5, anchor='center')

boss_ball_image = ImageTk.PhotoImage(Image.open('images/orb.png').resize((80, 80), Image.Resampling.LANCZOS))
player_1_ball_img = ImageTk.PhotoImage(Image.open('images/fireattack.png').resize((80,80), Image.Resampling.LANCZOS))
player_2_ball_img = ImageTk.PhotoImage(Image.open('images/fireattack.png').resize((40,40), Image.Resampling.LANCZOS))
boss_image = ImageTk.PhotoImage(Image.open('images/boss.png').resize((140, 140), Image.Resampling.LANCZOS))
player_image1 = ImageTk.PhotoImage(Image.open('images/Dude_Monster.png').resize((60, 60), Image.Resampling.LANCZOS))
player_image2 = ImageTk.PhotoImage(Image.open('images/Pink_Monster.png').resize((60, 60), Image.Resampling.LANCZOS))

player_1_ball = Label(game_area, image=player_1_ball_img)
player_2_ball = Label(game_area, image=player_2_ball_img)
boss_ball = Label(game_area, image = boss_ball_image)
boss = Label(game_area, image = boss_image)
hero_1 = Label(game_area, image = player_image1)
hero_2 = Label(game_area, image = player_image2)
message = Label(game_area, style = 'Message.TLabel')
info_1 = Label(window)
info_2 = Label(window)

game_state = {
    'me': None,
    'opponent': None,
    'is_server': None,
    'shared': {
        'boss_x': 800,
        'boss_y': 300,
        'hero_1_y': 0,
        'hero_2_y': 100,
        'hero_1_x': 0,
        'hero_2_x': 0,
        'player_1_ball_x': 500,
        'player_1_ball_y': 230,
        'boss_ball_x': 700,
        'boss_ball_y': 200,
        'player_1': '',
        'player_2': '',
        'lives_1': 100,
        'lives_2': 500,
        'game_over_message': ''
    }
}

def get_opponent_and_decide_game_runner(user, message):
    # who is the server (= the creator of the channel)
    if 'created the channel' in message:
        name = message.split("'")[1]
        game_state['is_server'] = name == game_state['me']
    # who is the opponent (= the one that joined that is not me)
    if 'joined channel' in message:
        name = message.split(' ')[1]
        if name != game_state['me']:
            game_state['opponent'] = name

# handler for network messages
def on_network_message(timestamp, user, message):
    if user == 'system': 
        get_opponent_and_decide_game_runner(user, message)
    # key_downs (only of interest to the server)
    global keys_down_me, keys_down_opponent
    if game_state['is_server']:
        if user == game_state['me'] and type(message) is list:
            keys_down_me = set(message)
        if user == game_state['opponent'] and type(message) is list:
            keys_down_opponent = set(message)
    # shared state (only of interest to the none-server)
    if type(message) is dict and not game_state['is_server']:
        game_state['shared'] = message
        redraw_screen()

# remember which keys are down
keys_down_me = set()
keys_down_opponent = set()
keys_down = set() # locally
last_down = None

def on_key_down(keycode):
    global last_down
    last_down = keycode
    if keycode in keys_down: return
    # add key that is down to keys_down
    keys_down.add(keycode)
    send(list(keys_down)) # send keys down via network

def on_key_up(keycode):
    global last_down
    # ignore false release / auto-repeat
    # (a release that is followed by a down in 
    # in less than 0.01 seconds is considered false)
    last_down = None
    tk_sleep(window, 1 / 1000) 
    if last_down == keycode: return
    if keycode not in keys_down: return
    # remove key that is relased from keys_down
    keycode in keys_down and keys_down.remove(keycode)
    send(list(keys_down)) # send keys down via network


window.bind('<Up>', lambda e: on_key_down(38))
window.bind('<KeyRelease-Up>', lambda e: on_key_up(38))
window.bind('<Down>', lambda e: on_key_down(40))
window.bind('<KeyRelease-Down>', lambda e: on_key_up(40))
window.bind('<Left>', lambda e: on_key_down(37))
window.bind('<KeyRelease-Left>', lambda e: on_key_up(37))
window.bind('<Right>', lambda e: on_key_down(39))
window.bind('<KeyRelease-Right>', lambda e: on_key_up(39))

# Draw the elements on the screen 
def redraw_screen():
    boss_x, boss_y, hero_1_y, hero_2_y, hero_1_x, hero_2_x, player_1_ball_x, player_1_ball_y, boss_ball_x, boss_ball_y,\
        player_1, player_2, lives_1, lives_2,\
        game_over_message =\
            game_state['shared'].values()


    boss.place(x=boss_x, y=boss_y)
    boss_ball.place(x=boss_ball_x, y=boss_ball_y)
    hero_1.place(x=hero_1_x, y=hero_1_y)
    hero_2.place(x=hero_2_x, y=hero_2_y)
    player_1_ball.place(x=player_1_ball_x, y=player_1_ball_y)
    info_1.config(text = (
       f'\nPlayer 1: {player_1}\n'+
       f'Player 2: {player_2[0:10]}\n' +
       f'Lives: {lives_1}'
    ))
    info_2.config(text = (
       f'\nBoss: Python\n' +
       f'Lives: {lives_2}'
    ))
    info_1.place(x = 50, y = game_area_height + 50)
    info_2.place(x = game_area_width - 100, y = game_area_height + 50)
    if game_over_message != '':
        message = Label(game_area, style = 'Message.TLabel')
        message.config(text = game_over_message)
        message.place(y = 200, x = 100, width = game_area_width - 200)

def game_loop():
    # unpack game_state['shared'] to variables
    shared = game_state['shared']
    boss_x, boss_y, hero_1_y, hero_2_y, hero_1_x, hero_2_x, player_1_ball_x, player_1_ball_y, boss_ball_x, boss_ball_y= list(shared.values())[0:10]
    # who is player 1 (= me) and 2 (= opponent)
    shared['player_1'] = game_state['me']
    shared['player_2'] = game_state['opponent']
    boss_x_direction = 1
    boss_y_direction = 1
    player_1_ball_x_direction = 1
    player_1_ball_y_direction = 1
    boss_ball_x_direction = 1
    boss_ball_y_direction = 1
    while True:
        # run the loop 24 times per second
        tk_sleep(window, 1 / 24)
        # move all the entities
        boss_x += 10 * boss_x_direction
        boss_y += 10 * boss_y_direction
        if boss_x >= game_area_width - 140: 
            boss_x_direction = -1
        if boss_x <= 0:
            boss_x_direction = 1
        if boss_y >= game_area_height - 140: 
           boss_y_direction = -1
        if boss_y <= 0:
            boss_y_direction = 1
        boss_ball_x += 10 * boss_ball_x_direction
        boss_ball_y += 10 * boss_ball_y_direction
        if boss_ball_x >= game_area_width - 80: 
            boss_ball_x_direction = -1
        if boss_ball_x <= 0:
            boss_ball_x_direction = 1
        if boss_ball_y >= game_area_height - 80: 
           boss_ball_y_direction = -1
        if boss_ball_y <= 0:
            boss_ball_y_direction = 1  
        player_1_ball_x += 10 * player_1_ball_x_direction
        player_1_ball_y += 10 * player_1_ball_y_direction
        if player_1_ball_x >= game_area_width - 80:
            player_1_ball_x_direction = -1
        if player_1_ball_x <= 0:
            player_1_ball_x_direction = 1
        if player_1_ball_y >= game_area_height - 80:
            player_1_ball_y_direction = -1
        if player_1_ball_y <= 0:
            player_1_ball_y_direction = 1
        
        # move player 1, 38 = up arrow, 40 = down arrow, 37 = left arrow, 39 = right arrow
        if 38 in keys_down_me and hero_1_y >= 10:
            hero_1_y -= 20
        if 40 in keys_down_me and hero_1_y <= game_area_height - 80:
            hero_1_y += 20
        if 37 in keys_down_me and hero_1_x >= 10:
            hero_1_x -= 20
        if 39 in keys_down_me and hero_1_x <= game_area_width - 40:
            hero_1_x += 20
        # move player 2
        if 38 in keys_down_opponent and hero_2_y >= 10:
            hero_2_y -= 20
        if 40 in keys_down_opponent and hero_2_y <= game_area_height - 80:
            hero_2_y += 20
        if 37 in keys_down_opponent and hero_2_x >= 10:
            hero_2_x -= 20
        if 39 in keys_down_opponent and hero_2_x <= game_area_width - 40:
            hero_2_x += 20
        
        # check if boss hits players    
        if (boss_x + 100 > hero_1_x and boss_x < hero_1_x + 60 and boss_y + 100 > hero_1_y and boss_y < hero_1_y + 60):
            shared[f'lives_1'] -= 2
        if (boss_x + 100 > hero_2_x and boss_x < hero_2_x + 60 and boss_y + 100 > hero_2_y and boss_y < hero_2_y + 60):
            shared[f'lives_1'] -= 2

        # check if orb is hitting players
        if (boss_ball_x + 80 > hero_1_x and boss_ball_x < hero_1_x + 60 and boss_ball_y + 80 > hero_1_y and boss_ball_y < hero_1_y + 60):
            shared[f'lives_1'] -= 1
        if (boss_ball_x + 80 > hero_2_x and boss_ball_x < hero_2_x + 60 and boss_ball_y + 80 > hero_2_y and boss_ball_y < hero_2_y + 60):
            shared[f'lives_1'] -= 1
            
        # check if the fire hits boss   
        if (player_1_ball_x + 80 > boss_x and player_1_ball_x < boss_x + 100 and player_1_ball_y + 80 > boss_y and player_1_ball_y < boss_y + 100):
            shared[f'lives_2'] -= 5
        # check if orb hits boss
        if (boss_ball_x + 80 > boss_x and boss_ball_x < boss_x + 100 and boss_ball_y + 80 > boss_y and boss_ball_y < boss_y + 100):
            shared[f'lives_2'] += 1
            
        # check if the fire hits the players
        if (player_1_ball_x + 80 > hero_1_x and player_1_ball_x < hero_1_x + 80 and player_1_ball_y + 80 > hero_1_y and player_1_ball_y < hero_1_y + 80):
            shared[f'lives_1'] += 1
        if (player_1_ball_x + 80 > hero_2_x and player_1_ball_x < hero_2_x + 80 and player_1_ball_y + 80 > hero_2_y and player_1_ball_y < hero_2_y + 80):
            shared[f'lives_1'] += 1
        
    
        if shared[f'lives_1'] == 0:
                shared['game_over_message'] =\
                    'You have lost!'
        if shared[f'lives_2'] == 0:
                shared['game_over_message'] = 'You have bested the mighty beast!'
        # repack variables to game_state['shared']
        shared['boss_x'] = boss_x
        shared['boss_y'] = boss_y
        shared['hero_1_y'] = hero_1_y
        shared['hero_2_y'] = hero_2_y
        shared['hero_1_x'] = hero_1_x
        shared['hero_2_x'] = hero_2_x
        shared['player_1_ball_x'] = player_1_ball_x
        shared['player_1_ball_y'] = player_1_ball_y
        shared['boss_ball_x'] = boss_ball_x
        shared['boss_ball_y'] = boss_ball_y
        # send state
        send(game_state['shared'])
        # redraw screen
        redraw_screen()
        # the game is over if there is a game over message
        if shared['game_over_message'] != '':
            break

# start - before game loop
def start():
    # hide some things initially
    ### j('.wait, .ball, .paddle-1, .paddle-2').hide()
    # show the content/body (hidden by css)
    ### j('body').show()
    # connect to network
    game_state['me'] = simpledialog.askstring(
        'Input', 'Your user name', parent=window)
    # note: adding prefix so I don't disturb
    # other class mates / developers using the same
    # network library
    channel = 'ironboy_pong_' + simpledialog.askstring(
        'Input', 'Channel', parent=window)
    connect(channel, game_state['me'], on_network_message)
    message.config(text = 'Waiting for an opponent...')
    message.place(y = 200, x = 100, width = game_area_width - 200)
    # wait for an opponent 
    while game_state['opponent'] == None:
        tk_sleep(window, 1 / 10)
    message.destroy()
    # start game loop if i am the server
    if game_state['is_server']:
        game_loop()

# start
start()
start_window_loop(window)
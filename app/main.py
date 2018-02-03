# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import bottle
import os
import sys
import random
from pprint import pprint
from AStar import *

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    board_width = data['width']
    board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    # TODO: Do things with data

    return {
        'color': '#%06X' % random.randint(0,256**3-1),
        'taunt': '{} ({}x{})'.format(game_id, board_width, board_height),
        'head_url': 'https://cn.pling.com/img//hive/content-pre1/104822-1.png',
        'name': 'Winding Constrictor %i' % random.randint(0,255),
	'head_type': 'tongue',
	'tail_type': 'freckled',
    }


@bottle.post('/move')
def move():
    data = bottle.request.json

    # TODO: Do things with data
    directions = ['up', 'down', 'left', 'right']

    mysnek, grid = init(data)

    myhead = mysnek['coords'][0]
    
    # Eliminate completly unsafe directions
    # Walls, and other snakes
    for direction in directions[:]:
        x = myhead[0]
        y = myhead[1]
        if direction == 'up':
            y -= 1
        if direction == 'down':
            y += 1
        if direction == 'left':
            x -= 1
        if direction == 'right':
            x +=1

	# Avoid walls
        if x < 0 or x >= data['width']:
            directions.remove(direction)
            continue
        if y < 0 or y >= data['height']:
            directions.remove(direction)
            continue

	# Avoid snake tails
        if grid[x][y] == 'X':
	    directions.remove(direction)
            continue

	# Avoid places snakes may move
	if grid[x][y] == '!':
            directions.remove(direction)
            continue

    #pprint (data)
    pprint (zip(*grid), width=120)
    #pprint (directions)

    move = random.choice(directions)
    print move
    return {
        'move': move,
        'taunt': 'battlesnake-python!'
    }

def init(data):
    grid = [['.' for col in xrange(data['height'])] for row in xrange(data['width'])]
    for snek in data['snakes']:
        if snek['id'] == data['you']:
            mysnek = snek
        else:
            # Mark off possible sneak moves
            coord = snek['coords'][0]
            directions = ['up', 'down', 'left', 'right']
            for direction in directions:
                x = coord[0]
                y = coord[1]
                if direction == 'up':
                    y -= 1
                if direction == 'down':
                    y += 1
                if direction == 'left':
                    x -= 1
                if direction == 'right':
                    x +=1

                # Skip out of bounds
                if x < 0 or x >= data['width']:
                    continue
                if y < 0 or y >= data['height']:
                    continue

                # Set marker for unsafe space
                grid[x][y]="!"

	# Mark off snake positions
        for coord in snek['coords']:
            grid[coord[0]][coord[1]] = 'X'

    for food in data['food']:
        grid[food[0]][food[1]] = '='
    
    return mysnek, grid

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))

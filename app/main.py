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
    move = False


    mysnek, grid = init(data)

    myhead = mysnek['coords'][0]

    # Go to food if possible
    path = a_star(mysnek['coords'][0], data['food'][0], grid, mysnek['coords'])
    if path:
        move = dirToCoord(mysnek['coords'][0], path[1])
    #print mysnek['coords'][0]
    #print path[1]
    #print dirToCoord(mysnek['coords'][0], path[1])

    # If no path to food, fall back to safer moves
    if not move:
        directions = ['up', 'down', 'left', 'right']
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

        # Check for unfavorable moves
        if len(directions) > 0:
            directions2 = directions[:]
            for direction in directions2[:]:
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
                # Avoid places snakes may move
                if grid[x][y] == '!':
                    directions2.remove(direction)
                    continue
            if len(directions2) > 0:
                # Make a random move
                move = random.choice(directions2)
            else:
                print '\033[91m' + "Must move unsafe!" + '\033[0m'
                # Make a random move
                move = random.choice(directions)
        else:
            # Make a random move
            move = random.choice(directions)

    #pprint (data)
    pprint (zip(*grid), width=120)
    #pprint (directions)

    print move
    return {
        'move': move,
        'taunt': move
    }

def init(data):
    # Create empty grid to hold flags
    grid = [['.' for col in xrange(data['height'])] for row in xrange(data['width'])]

    # Mark foods
    # First so its overwritten by unsafe flags
    for food in data['food']:
        grid[food[0]][food[1]] = '='

    # Find myself
    for snek in data['snakes']:
        if snek['id'] == data['you']:
            mysnek = snek
            break

    # Set flags
    for snek in data['snakes']:

        # Mark off possible moves of opponents
        if snek['id'] != data['you']:
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

                # If snek is smaller, eat it
                if len(mysnek['coords']) > len(snek['coords']):
                    grid[x][y]="S"
                else:
                    # Set marker for unsafe space
                    grid[x][y]="!"

	# Mark off snake positions
        for coord in snek['coords']:
            grid[coord[0]][coord[1]] = 'X'


    return mysnek, grid

def dirToCoord(from_cell, to_cell):
    dx = to_cell[0] - from_cell[0]
    dy = to_cell[1] - from_cell[1]

    if dx == 1:
        return 'right'
    elif dx == -1:
        return 'left'
    elif dy == -1:
        return 'up'
    elif dy == 1:
        return 'down'

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))

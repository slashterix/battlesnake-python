# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import bottle
import os
import sys
import random
from pprint import pprint
from moveconvert import move2018to2017
from AStar import *

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')

@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        #'color': '#%06X' % random.randint(0,256**3-1),
        'color': '#000000',
        'secondary_color': '#FFD700',
        'taunt': '{}'.format(game_id),
        #'head_url': 'https://cn.pling.com/img//hive/content-pre1/104822-1.png',
        'head_url': head_url,
        'name': 'Make Snek Great Again!',
        'head_type': 'shades',
        'tail_type': 'freckled',
        #'head_type': random.choice(["bendr", "dead", "fang", "pixel", "regular", "safe", "sand-worm", "shades", "smile", "tongue"]),
        #'tail_type': random.choice(["small-rattle", "skinny-tail", "round-bum", "regular", "pixel", "freckled", "fat-rattle", "curled", "block-bum"]),
    }


@bottle.post('/move')
def move():
    data = move2018to2017(bottle.request.json)
    move = False
    path = False

    mysnek, grid = init(data)

    # Print debug game board
    pprint (zip(*grid), width=120)

    myhead = mysnek['coords'][0]

    # Go to food if possible
    for food in data['food']:
        # Get path to food item
        t_path = a_star(mysnek['coords'][0], food, grid, mysnek['coords'])
        # If path is shorter than previous food path, choose it
        if not path or t_path and len(path) > len(t_path):
            path = t_path

    # Set the move for the path
    if path:
        move = dirToCoord(mysnek['coords'][0], path[1])

    # Go to tail if no food move available
    if not move:
        path = a_star(mysnek['coords'][0], mysnek['coords'][-1], grid, mysnek['coords'])
        # There may be no path to the tail
        if path:
            move = dirToCoord(mysnek['coords'][0], path[1])

    # If still no paths, fall back to safer moves
    if not move:
        directions = ['up', 'down', 'left', 'right']

        # Eliminate completely unsafe directions
        # Walls, and other snakes
        for direction in directions[:]:
            print direction
            pprint(myhead)
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
            print "X is ", x, " and width is ", data['width']
            if x < 0 or x >= data['width']:
                directions.remove(direction)
                continue
            print "Y is ", y, " and height is ", data['height']
            if y < 0 or y >= data['height']:
                directions.remove(direction)
                continue

            # Avoid snake tails
            if grid[x][y] == 'X':
                print "Tail avoidance"
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
                # No safe moves, pick a possible head collision and hope for the best
                move = random.choice(directions)
        else:
            # Give up and guess at random
            move = random.choice(['up', 'down', 'left', 'right'])

    # Print the move we are making
    print move

    return {
        'move': move
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

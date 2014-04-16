from PIL import Image, ImageDraw
from pug.nlp import db_decision_tree as dt
from pug.db.explore import count_unique


def draw_tree(tree, path='tree.jpg'):
    w = dt.get_width(tree) * 100
    h = dt.get_depth(tree) * 100 + 120

    img = Image.new('RGB',(w, h),(255,255,255))
    draw = ImageDraw.Draw(img)

    draw_node(draw, tree, w / 2,20)
    img.save(path,'JPEG')


def draw_node(draw, tree, x, y):
    if tree.results == None:
        # Get the width of each branch
        w1 = dt.get_width(tree.fb) * 100
        w2 = dt.get_width(tree.tb) * 100

        # Determine the total space required by this node
        left = x - (w1 + w2) / 2
        right = x + (w1 + w2) / 2

        # Draw the condition string
        draw.text((x - 20, y - 10), str(tree.col) + ':' + str(tree.value),(0,0,0))

        # Draw links to the branches
        draw.line((x, y, left + w1 / 2, y + 100), fill = (255,0,0))
        draw.line((x, y, right - w2 / 2, y + 100), fill = (255,0,0))

        # Draw the branch nodes
        draw_node(draw, tree.fb, left + w1 / 2, y + 100)
        draw_node(draw, tree.tb, right - w2 / 2, y + 100)
    else:
        txt = ' \n'.join(['%s:%d'%v for v in tree.results.items()])
        draw.text((x - 20, y), txt,(0,0,0))


def classify(observation, tree):
    if tree.results != None:
        return tree.results
    else:
        v = observation[tree.col]
        branch = None
        if isinstance(v, int) or isinstance(v, float):
            if v >= tree.value: branch = tree.tb
            else: branch = tree.fb
        else:
            if v == tree.value: branch = tree.tb
            else: branch = tree.fb
        return classify(observation, branch)

def prune(tree, mingain):
    # If the branches aren't leaves, then prune them
    if tree.tb.results == None:
        prune(tree.tb, mingain)
    if tree.fb.results == None:
        prune(tree.fb, mingain)
        
    # If both the subbranches are now leaves, see if they
    # should merged
    if tree.tb.results != None and tree.fb.results != None:
        # Build a combined dataset
        tb, fb = [],[]
        for v, c in tree.tb.results.items():
            tb += [[v]] * c
        for v, c in tree.fb.results.items():
            fb += [[v]] * c
        
        # Test the reduction in entropy
        delta = dt.entropy(tb + fb) - (dt.entropy(tb) + dt.entropy(fb) / 2)

        if delta < mingain:
            # Merge the branches
            tree.tb, tree.fb = None, None
            tree.results = count_unique(tb + fb)


def mdclassify(observation, tree):
    if tree.results != None:
        return tree.results
    else:
        v = observation[tree.col]
        if v == None:
            tr, fr = mdclassify(observation, tree.tb), mdclassify(observation, tree.fb)
            tcount = sum(tr.values())
            fcount = sum(fr.values())
            tw = float(tcount) / (tcount + fcount)
            fw = float(fcount) / (tcount + fcount)
            result = {}
            for k, v in tr.items():
                result[k] = v*tw
            for k, v in fr.items():
                result[k] = v*fw            
            return result
        else:
            if isinstance(v, int) or isinstance(v, float):
                if v >= tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            else:
                if v == tree.value:
                    branch = tree.tb
                else:
                    branch = tree.fb
            return mdclassify(observation, branch)



def get(obj, key, default=None):
    try:
        # integer key and sequence (list) object
        return obj[key]
    except:
        if isinstance(obj, dict):
            try:
                return obj.get(key, default)
            except:
                return obj.get(tuple(obj)[key], default) 
    return obj.getattr(key, default)
    

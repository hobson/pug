import sys, csv, pickle
from nltk.metrics import edit_distance

def remove_space(csv_name):
  with open(csv_name, 'r') as read_file:
    write_file = open('new.txt', 'w')
    current = ''
    for line in read_file:
      marker = line.find('\r')
      while marker != -1:
        line = line[0:marker] + line[marker+1:]
        marker = line.find('\r')
      write_file.write(line)
      #if line.find('LC70') == -1:
      #  current = current + line
      #else:
      #  write_file.write(current)
      #  current = line       
  write_file.close()
  
def check(database, phrase, threshold):
  score = float('inf')
  output = ' '
  counter = -1
  for entry in database:
    counter += 1
    current_score = float(edit_distance(entry, phrase))/(1+max(len(phrase), len(entry)))
    if current_score < score:
      score = current_score
      output = entry
  if score <= threshold:
    return counter
  else:
    return 0
    
def outcome_map1(outcome):
  if outcome == 'PART':
    return true
  else:
    return false
    
def main():
  # remove_space('asdf.txt')
  args = sys.argv[1:]
  csv_name = args[0]
  threshold = 0.4
  database = []
  diagnosis = []
  outcome = []
  with open(csv_name, 'r') as csv_file:
    spamreader = csv.reader(csv_file, delimiter=',', quotechar='|')
    for row in spamreader:
      if(len(row[2]) != 0):
        junk_text = 'ts:'
        junk_position = row[1].find(junk_text)
        if junk_position != -1:
          row[1] = row[1][junk_position+len(junk_text):]
        junk_position = row[1].find('Q01')
        if junk_position != -1:
          row[1] = row[1][0:junk_position]
        check_result = check(database, row[1], threshold)
        if check_result == 0:
          database.append(row[1])
          diagnosis.append(len(database)-1)
        else:
          diagnosis.append(check_result)
        outcome.append(row[2])
  with open('data.pckl', 'w') as f:
    pickle.dump([database, diagnosis, outcome], f)
  
  
if __name__ == '__main__':
  main()
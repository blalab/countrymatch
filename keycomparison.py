# keycomparison.py

import csv
from editdistance import editdistance

threshold = 4

d = editdistance()
candidates = []

needles = 'key_x.csv'
haystack = 'key_y.csv'
map = 'results.csv'
nomap = 'noresults.csv'


def csv_writer(rows,path,mode):
    with open(path, mode) as csv_file:
        print('Writing '+str(len(rows))+' rows into '+path)
        for l in rows:
            writer = csv.writer(csv_file, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(l)

# Reset existing map
csv_writer([],map,'w')
csv_writer([],nomap,'w')

with open(needles, 'rb') as f:
    reader_x = csv.reader(f)
    for r in reader_x:
        id_x = r[0]
        country_x = r[1]
        province_x = r[2]
        city_x = r[3]
        key_x = country_x+' '+province_x+' '+city_x
        print('Matching:'+ key_x)

        with open(haystack, 'rb') as m:
            reader_y = csv.reader(m)
            candidates = [] 
            distances = []

            for q in reader_y:
                id_y = q[0]
                country_y = q[1]
                province_y = q[2]
                city_y = q[3]
                key_y = country_y+' '+province_y+' '+city_y 

                if key_x.lower() == key_y.lower():
                    # There is an exact match. No need to calculate edit distance

                    print('Match for: %s, %s,%s. %s maps to %d',
                          (country_x,province_x,city_x,id_x,id_y))

                    distances.append(0)
                    break
                    
                else:

                    edistance = d.ed(key_x.lower(),key_y.lower())
                    distances.append(edistance)

                    if edistance <= threshold:
                        line = [edistance,id_x,key_x,id_y,key_y]
                        candidates.append(line)
                        print(line)

            st=(' Min:'+str(min(distances))+
                  ' Max:'+str(max(distances))+
                  ' Len:'+str(len(distances))+
                  ' Avg:'+str(sum(distances)/len(distances)))

            print(st)
                
            if len(candidates)!=0:
                csv_writer(candidates,map,'a')
            else:
                print('No candidates found')
                line = [id_x,country_x,province_x,city_x,min(distances),max(distances)]

                csv_writer([line],nomap,'a')

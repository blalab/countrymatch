# countrymatch
Match two country datasets using Python CSV and Edit Distance 

## Mapping two different country datasets with Python CSV

The problem:  There are two companies , lets call them X and Y. Both of them have proprietary City IDs. Of course the moment comes when they need to do business but they can’t share any information because their City IDs are not the same. Lets just create a dictionary that translates from one A to B right? Yes but not so fast. The solution is not as straightforward as it appears to be. In a real case scenario you’ll find dirty, non-normalized, legacy, incorrect, incomplete, sparse data from both parts. Good luck we have python =)

###Company X data 

Data lives in a MySQL database. 

I won’t go through each one of the MySQL table’s schema. But this is as much relevant data I can get from their database:

```
SELECT c.CityCode, c.CityName, c.CityDescription, c.State,c.Area , y.country, y.CountryCode
FROM tblCity as c, tblCountry as y 
WHERE c.Country=y.CountryID
INTO OUTFILE '/tmp/TA_cities.csv'
FIELDS ENCLOSED BY '"' TERMINATED BY ','
LINES TERMINATED BY ‘\n’;
```

Returns something like this:

```
"ABQ","Albuquerque, NM","","USA","USA"
"ABR","Aberdeen, SD","","USA","USA"
"ACA","Acapulco, MEXICO","","MEXICO","MEX"
"ACY","Atlantic City, NJ","","USA","USA"
"ADE","*Ste-Adele, QC, CANADA","","CANADA","CAN"
"ADQ","ADQ-Kodiak, AK","AK","USA","USA"
"ADS","Addison, TX","","USA","USA"
"ADZ","San Andres,Colombia","","COLOMBIA","COL"
"AGH","Agoura Hills, CA","","USA","USA"
"AHN","Athens, GA","","USA","USA"
"AJU","ARACAJU, BRAZIL","","BRAZIL","BRA"
"ALB","Albany, NY","","USA","USA"
"ALG","Algarrobo, CHILE”,"","CHILE","CHL"
…
```


Lets analyze this a little bit:
The first column is the CompanyX’s CityID. We won’t touch that
The second column has both the name of the city and the state code serialized in the same string (comma separated)
For countries that are not USA or Canada,  the serialization convention of the second place being the State 2 letter code is not respected, instead the name of the country is place there (why they did that if there is already an explicit country field? I don’t know)
The third column seems to be pretty useless. Its supposed to have the “state” but it is rarely used. We will use the state from the second column’s string. Such sparse columns are not to be trusted because they are not actively maintained. This looks like a failed attempt to de-normalize the other column. 
The fourth and fifth columns seem to be the long and short name for a country. Of course it was to much to ask for “United States” or “United States of America” and they used “USA” as the long name as well. I point this out because you’ll see the other company does use long names correctly and we will have to fix this.




###Company Y data 

Company Y has sent their data in a CSV file and it has the following format:

```
Country ID,CountryEnName,Province ID,ProvinceEnName, City Code,CityEnName
66,United States,10299,Georgia,80355,Vienna
66,United States,10287,New Jersey,80394,Westfield
66,United States,10253,Tennessee,80395,Winchester
47,Canada,10149,Quebec,78051,Saint-Raphael
47,Canada,10282,New Brunswick,78149,Pointe-du-Chene
47,Canada,10203,Newfoundland and Labrador,78431,Cow Head
47,Canada,10149,Quebec,78434,Saint-Damien-de-Buckland
47,Canada,10034,Alberta,78902,Lloydminster
72,Mexico,10690,Querétaro,77719,Colon
72,Mexico,10686,Jalisco,78565,El Limoncito
72,Mexico,10692,Nayarit,78566,Los Ayala
…
```


The first column is their proprietary CountryID. A brief google search shows that it is not a standard ID like the CountryCode used to call these countries. You can always hope they are using well known standard IDs =)
Second Column is the long name of the country in english, that is good news, we are going to use this one to correlate the country.
I don’t know is Province ID in the third column is something we could use. I have the feeling it is also proprietary. It will help us to differentiate in case there are two New Jerseys in the USA =)
Fourth column is the Company Y’s City proprietary ID. This is exactly the ID we want to map against the Company X city ID.
The name of the city in english. This is what we will use to match the cities against the other company list. 


##Strategy

Both datasets seem to have three entities in common: City Name, Province Name and Country Name. Usually the more you have in common the easier it is to map. If you are lucky you’ll find that both datasets use an standardized id in common but it is not the case here. 

In both datasets, we will make a composed key with the Country Name, Province Name and the City Name. The chances of having two cities with the same name in the same Country and Province are not zero but they are low enough.

Once both dataset’s keys are ready we will compare them using an “edit distance” algorithm. 

Lets set an explicit format for the key:
Countries, Province and Name are to be in english language
No abbreviations. We will use the longest name possible for each one of them.


###Preparing Company X’s key


Country: Since the last column has what seems to be the 3 letter ISO Code for countries we will use that one. We are going to need an auxiliary dataset that translates the 3 letter code to the long name in English. Once we have it we will compare it with what’s in the 4th column. For cases like “USA”, our program will detect a discrepancy and alert us. Later on you’ll check the alerts and decide whether the assumption made by the program was correct. 

Province:  Also known as “State” in the US , this piece of information is serialized in the second column for US and Canada cities and for the rest of the countries it is just not existing. We will also have to expand it into its long version. 

City: This column is very dirty, Canada cities seem to have an asterisk (*) at the beginning of the name and US cities have the 3 letter state code prefixed and joined with a Dash. We need to get rid of all that. Also non US or Canada Cities have the country (non abbreviated) serialized with a comma. This is the ultimate Legacy column =)



Finally… lets write some code

We go to the inter webs and using duckgogo I find this:
http://www.fonz.net/blog/archives/2008/04/06/csv-of-states-and-state-abbreviations/

This csv file has the following format. 

```
"State","Abbreviation"
"Alabama","AL"
"Alaska","AK"
"Arizona","AZ"
"Arkansas","AR"
"California","CA"
"Colorado","CO"
"Connecticut","CT"
“Delaware”,"DE"
…
```

which is exactly what we need. We save it in the same folder where you have the CSVs from the Company X and Company Y

Lets start writing the python module. First, we are going to create a dictionary of US cities

```
# citymap.py

import csv

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

```


Not is is turn for Canada. No luck this time searching the web. I’ll have to create that CSV myself. Luckily Canada list is pretty short. I open https://en.wikipedia.org/wiki/Canadian_postal_abbreviations_for_provinces_and_territories and start typing the CSV myself and save it in a file called ca_states.csv and save it in the same folder as the python module

```
"State","Abbreviation"
"Alberta","AB"
"British Columbia","BC"
"Manitoba","MB"
"New Brunswick","NB"
"Newfoundland and Labrador","NL"
"Nova Scotia","NS"
"Northwest Territories","NT"
"Nunavut","NU"
"Ontario","ON"
"Prince Edward Island","PE"
"Quebec","QC"
"Saskatchewan","SK"
“Yukon","YT"
...
```


We create a dictionary of Canadian for Provinces and/or Territories

```
# citymap.py

import csv

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

    ca_states = {}
    with open('ca_states.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            ca_states[r[1]] = r[0]

```

Lets do the same for countries. With a quick search in the internet I find this:

https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/slim-3/slim-3.csv


```
name,alpha-3,country-code
Afghanistan,AFG,004
Åland Islands,ALA,248
Albania,ALB,008
Algeria,DZA,012
American Samoa,ASM,016
Andorra,AND,020
Angola,AGO,024
Anguilla,AIA,660
Antarctica,ATA,010
Antigua and Barbuda,ATG,028
Argentina,ARG,032
Armenia,ARM,051
...
```

```
# citymap.py

import csv

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

    ca_states = {}
    with open('ca_states.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            ca_states[r[1]] = r[0]

    countries = {}
    with open('countries.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            countries[r[1]] = r[0]

```


In order to use the dictionaries we need to de-serialize the second column. We’ll split that second column in two. One with the City Name and the other one with the province name (if any).

Notice how we are outputting everything to another CSV file (key_x.csv) . That file contains all the elements of the Company X’s key that we will compare against Company Y’s key to build the map


```
# citymap.py
import csv

origin_x = 'cities_x_raw.csv'
key_x = 'key_x.csv'

def csv_writer(rows,path):
    with open(path, "w") as csv_file:
        print('Writing '+str(len(rows))+' rows into '+path)
        for l in rows:
            writer = csv.writer(csv_file, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(l)

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

    ca_states = {}
    with open('ca_states.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            ca_states[r[1]] = r[0]

    countries = {}
    with open('countries.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            countries[r[1]] = r[0]


    with open(origin_x, 'rb') as f:
        reader = csv.reader(f)
        out = []
        for row in reader:
            city_id = row[0]
            country = row[6]
           
            # We split the second column using the comma as separator
            parts = row[1].split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                province = parts[1].strip()

            out.append([city_id,country,province,city])

        csv_writer(out,key_x)

```

Run this program and open key_x.csv to see what we’ve achieved so far

```
"ABQ","USA","NM","Albuquerque"
"ABR","USA","SD","Aberdeen"
"ACA","MEX","MEXICO","Acapulco"
"ACY","USA","NJ","Atlantic City"
"ADE","CAN","QC","*Ste-Adele"
"ADQ","USA","AK","ADQ-Kodiak"
"ADS","USA","TX","Addison"
"ADZ","COL","Colombia","San Andres"
"AGH","USA","CA","Agoura Hills"
"AHN","USA","GA","Athens"
…
```


There is still some cleaning to do. We need to remove the Asterisk, remove the sufix that some US cities have and replace the state and country abbreviations for long names using the dictionaries we created before.

```
# citymap.py
import csv

origin_x = 'cities_x_raw.csv'
key_x = 'key_x.csv'

def csv_writer(rows,path):
    with open(path, "w") as csv_file:
        print('Writing '+str(len(rows))+' rows into '+path)
        for l in rows:
            writer = csv.writer(csv_file, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(l)

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

    ca_states = {}
    with open('ca_states.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            ca_states[r[1]] = r[0]

    countries = {}
    with open('countries.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            countries[r[1]] = r[0]


    with open(origin_x, 'rb') as f:
        reader = csv.reader(f)
        out = []
        for row in reader:
            city_id = row[0]
            country = row[6]
           
            # We split the second column using the comma as separator
            parts = row[1].split(',')
            if len(parts) >= 2:

                city = parts[0].strip()
                province = parts[1].strip()

            # Removing the asterisk
            if city[:1]=='*': 
                city = city[1:]

            # Removing the US city sufix
            parts = city.split('-')
            if len(parts)>1:
                city = parts[1].strip()

            # Replacing abbreviations for long names using the dictionaries
            
            if province.upper() in us_states and country=='USA':
                province = us_states[province.upper()]
            elif province.upper() in ca_states and country=='CAN':
                province = ca_states[province.upper()]
            else:
                province = ''

            if country.upper() in countries:
                country = countries[country.upper()]
           
            out.append([city_id,country,province,city])

        csv_writer(out,key_x)
```


The key_x.csv looks like this now:

```
"ABQ","United States of America","New Mexico","Albuquerque"
"ABR","United States of America","South Dakota","Aberdeen"
"ACA","Mexico","","Acapulco"
"ACY","United States of America","New Jersey","Atlantic City"
"ADE","Canada","Quebec","Adele"
"ADQ","United States of America","Alaska","Kodiak"
"ADS","United States of America","Texas","Addison"
"ADZ","Colombia","","San Andres"
"AGH","United States of America","California","Agoura Hills"
"AHN","United States of America","Georgia","Athens"
"AJU","Brazil","","ARACAJU"
"ALB","United States of America","New York","Albany"
"ALG","Chile","","Algarrobo"
...
```


Non US or Canada cities have empty entities. We could scrap wikipedia and start subtracting this information from similar sources but we will cover that topic which is extremely interesting in another post.

For the time being we are going to make the (absurd?) assumption that there are no cities with identical name in the rest of the world in the same country.

Not it is time to focus in Company Y

###Preparing Company Y’s key

Fortunately for us, Company Y has a more standard list of cities. You’ll find yourself almost always adapting the less conventional dataset to the more conventional dataset. 

```
# citymap.py
import csv

origin_x = 'cities_x_raw.csv'
origin_y = 'cities_y_raw.csv'

key_x = 'key_x.csv'
key_y = 'key_y.csv'

def csv_writer(rows,path):
    with open(path, "w") as csv_file:
        print('Writing '+str(len(rows))+' rows into '+path)
        for l in rows:
            writer = csv.writer(csv_file, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(l)

if __name__ == "__main__":

    us_states = {}
    with open('us_states.csv', 'rb') as s:
        p = csv.reader(s)
        for r in p:
            us_states[r[1]] = r[0]

    ca_states = {}
    with open('ca_states.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            ca_states[r[1]] = r[0]

    countries = {}
    with open('countries.csv','rb') as s:
        p = csv.reader(s)
        for r in p:
            countries[r[1]] = r[0]


    with open(origin_x, 'rb') as f:
        reader = csv.reader(f)
        out = []
        for row in reader:
            city_id = row[0]
            country = row[6]
           
            # We split the second column using the comma as separator
            parts = row[1].split(',')
            if len(parts) >= 2:

                city = parts[0].strip()
                province = parts[1].strip()

            # Removing the asterisk
            if city[:1]=='*': 
                city = city[1:]

            # Removing the US city sufix
            parts = city.split('-')
            if len(parts)>1:
                city = parts[1].strip()

            # Replacing abbreviations for long names using the dictionaries
            
            if province.upper() in us_states and country=='USA':
                province = us_states[province.upper()]
            elif province.upper() in ca_states and country=='CAN':
                province = ca_states[province.upper()]
            else:
                province = ''

            if country.upper() in countries:
                country = countries[country.upper()]
           
            out.append([city_id,country,province,city])

        csv_writer(out,key_x)

    with open(origin_y, 'rb') as f:
        reader = csv.reader(f)
        out = []
        for row in reader:
            
            city_id= row[4]
            country = row[1]
            city = row[5]
            province = row[3]

            out.append([city_id,country,province,city])

        csv_writer(out,key_y)

```

key_y.csv that gets generated when you run the script looks like this:

```
"80388","Germany","Rhineland-Palatinate","Kradenbach"
"80389","Germany","Schleswig-Holstein","Kosel"
"80390","Germany","Lower-Saxony","Hameln"
"80391","Germany","Rhineland-Palatinate","Obersteinebach"
"80392","France","Burgundy","Levernois"
"3566","United Kingdom","North Yorkshire","York"
"80394","United States","New Jersey","Westfield"
"80395","United States","Tennessee","Winchester"
"80396","Kuwait","","Mahboula"
"80397","Bermuda","","Southampton"
...
```

###Comparing both keys

Great! Now we have two different files with (apparently) the same format. It is time to run one against the other. The last module prints the number of lines each CSV has. It shows something like this:

```
Writing 864 rows into key_x.csv
Writing 64272 rows into key_y.csv
```

The scenario looks like we will need 864 lookups in a list that is 64272 long. About 55 million operations. This is small since Company X is only focused in one continent while Company Y’s list cities worldwide. If both companies had the same scope we are seeing an O(n^2) situation. In that case, it would be about 4 billion operations. 

Should we remove from the list a city that has been matched? To make this faster? Not really. We need to know about those matches to improve the script or maybe find issues with the original source.

This is a one time mapping, speed is not exactly the top priority.

Should we avoid the extra step of placing the keys in a csv file and just run it from memory? Yes and no. For this example there would not be a problem but just imagine massive comparisons with millions of rows each. If you run out of memory and your program crashes you’ll have to redesign you program or get a bigger computer. See it as “good practice”.


###Writing the comparison module

We will use key_x.csv as the needles and key_y.csv as the haystack.

The first version of our comparison program will check if both keys are exactly the same with a simple “==” operation.

```

# keycomparison.py

import csv

candidates = []

needles = 'key_x.csv'
haystack = 'key_y.csv'

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
                    # There is an exact match.
                    print('Match for: %s, %s,%s. %s maps to %d',
                          (country_x,province_x,city_x,id_x,id_y))
                    break
               
```

Notice this program performs as many as m*n operations where m=864 and n=64272. However it finishes in about 3 minutes which is not that bad. 

The problem is that it only finds 565 matches out of 865 cities. That is about 65% effective. In a future update I'll go through different algorithms to improve that.





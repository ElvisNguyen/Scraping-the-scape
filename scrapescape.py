import requests
import pandas
import numpy as np
from bs4 import BeautifulSoup

def getShopLinks(url):
    #This is a list which will hold all the wiki links
    list = []
    
    #Grabs the Wiki page for all the shops
    html = requests.get(url)


    #Puts it into a beautiful soup object so we can parse the HTML
    beautifulSoupObj = BeautifulSoup(html.text, "lxml")


    #Uses beautiful soup's find function to narrow it down the the stuff we need to parse
    shops = beautifulSoupObj.find(id="mw-pages")





    #This var is the url for the next webpage containing the rest of the shops
    next = ""
    
    #This loop searches through all the a tags with an href and adds it to the list
    for link in shops.find_all('a'):
        current_link = link.get('href')
        if url == 'https://oldschool.runescape.wiki/w/Category:Shops':
            if "/w/Category:Shops?pagefrom=" not in current_link:
                list.append(current_link)
            else:
                next = current_link
        else:
            if "/w/Category:Shops?pageuntil" not in current_link:
                list.append(current_link)
                
    if next != "":
        next = 'https://oldschool.runescape.wiki'+next
        list = list + getShopLinks(next)

    return list

def getStoreData(url):
    #Grabs the Wiki page for the shop
    html = requests.get(url)
    
    
    
    #Puts it into a beautiful soup object so we can parse the HTML
    beautifulSoupObj = BeautifulSoup(html.text, "lxml")
    
    
    
    #print(beautifulSoupObj.prettify())
    
    
    
    #Finds the shop name from the header
    try:
        shopName = beautifulSoupObj.h1.string
    except AttributeError:
        pass
        
    #print(shopName)
    
    

    #Finds out if it's members only content
    try:
        members = beautifulSoupObj.find(lambda tag:tag.name=="th" and "Members" in tag.text).parent.td.string.rstrip("\n")
    except AttributeError:
        try:
            members = beautifulSoupObj.find(lambda tag:tag.name=="td" and "Members" in tag.text).parent.td.string.rstrip("\n")
        except AttributeError:
            return None
    #print(members)
    
    
    
    #Finds out if where the store is
    try:
        location = beautifulSoupObj.find(lambda tag:tag.name=="th" and "Location" in tag.text).parent.td.a.string
    except AttributeError:
        try:
            location = beautifulSoupObj.find(lambda tag:tag.name=="th" and "Location" in tag.text).parent.td.string
        except AttributeError:
            return None
    #print(location)
    
    
    
    #Narrows down the page's HTML to just the store's table
    table = beautifulSoupObj.find_all("table", {"class": "wikitable sortable"})
    
    #Reads the html into a dataFrame - powered by Pandas
    try:
        dataFrame = pandas.read_html(str(table))
    except ValueError:
        return None
        
    #Drops the column where the images were
    dataFrame[0].drop(dataFrame[0].columns[[0]], axis=1, inplace=True)
    
    #Adds Additional Data to DF
    try:
        dataFrame[0].insert(0, "Shop Name", shopName)
    except ValueError:
        pass
    try:
        dataFrame[0].insert(1, "Location", location)
    except ValueError:
        pass
    
    try:
        dataFrame[0].insert(0, "Members", members)
    except ValueError:
        pass
        
    #Renames the columns so that they're not ugly
    dataFrame[0].rename(columns={'Item.1': 'Item', 'Numberin stock': 'Number in stock', 'Pricesold at': 'Price sold at', 'Pricebought at': 'Price bought at'}, inplace=True)
    
    #print (dataFrame[0]) 
    
    return (dataFrame[0])
    
    #Writes the dataframe to a CSV file with the index column removed
    #dataFrame[0].to_csv(shopName+'.csv', index=False, header=shopName)
    
    #print(table)

def main():
    shopLinks = getShopLinks('https://oldschool.runescape.wiki/w/Category:Shops')
    column_names = ["Members", "Shop Name", "Location", "Item", "Number in stock", "Price bought at", "GE price"]
    merged = pandas.DataFrame(columns = column_names)
    
    for i in shopLinks:
        data = getStoreData('https://oldschool.runescape.wiki'+i)
        if data is not None:
            #Note: Append tried using 14GBs of Memory.... append calls concat then does magic...so we'll just knock it down a level and use concat / clean up manually
            merged = pandas.concat([merged, data], ignore_index=True) 
            print(data)
    
    try:
        index = np.r_[8:27]
        merged.drop(merged.columns[index], axis=1, inplace=True)
    except IndexError:
        try:
            index = np.r_[8:26]
            merged.drop(merged.columns[[8,26]], axis=1, inplace=True)
        except:
            pass
    
    
    merged['Shop -> GE Profit/Loss'] = np.subtract(pandas.to_numeric(merged['GE price'],errors='coerce'), pandas.to_numeric(merged['Price sold at'],errors='coerce') )
    merged['GE -> Shop Profit/Loss'] = np.subtract(pandas.to_numeric(merged['Price bought at'],errors='coerce'), pandas.to_numeric(merged['GE price'],errors='coerce') )
    merged.to_csv("Master shop list"+'.csv', index=False, header="Master Shop list")
main()
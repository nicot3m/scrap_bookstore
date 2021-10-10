#! /usr/bin/env python
# coding: utf-8

"""
scrap_bookstore(version 1.0.0)
Auteur: nicot3m
Date: 14/01/2021
This script extract data from online bookstore
(web scraping) using BeautifulSoup Python Library

Input:
    website https://books.toscrape.com
Output:
    csv files (one for each boo category)
    image files of each book
"""

#Importing modules and packages

import requests
from bs4 import BeautifulSoup as bs
import re
import csv
from pathlib import Path
import os


#Declaring global constants

URL_HOME="https://books.toscrape.com"
MAIN_DIR="Bookstoscrape"


#Defining functions

#Step1 scraping one book page and save data in csv file

def scrap_page_book(url_book):
    """
    Scrap a book page searching for book data 
    Input: url_book
    Output: dict_book
    """
    
    response_url_book=requests.get(url_book)
    
    if not response_url_book.ok:
        print("wrong url, cannot scrap this page book,",url_book)
        exit()
        
    else:
        soup_book=bs(response_url_book.content, "lxml") #content instead of text for encoding
        tag_book_table=soup_book.find("table", class_="table table-striped").findAll("td") #For upc, prices and stock
        tag_book_upc=tag_book_table[0].text
        tag_book_price_with_tax=tag_book_table[3].text
        tag_book_price_wo_tax=tag_book_table[2].text
        tag_book_stock=(tag_book_table[5].text).replace("In stock (","").replace(" available)","")
        tag_book_title=(soup_book.find("div",class_="col-sm-6 product_main").find("h1")).text
        tag_book_description=soup_book.find("meta",attrs={"name":"description"})["content"]
        tag_book_category=(soup_book.find("ul", class_="breadcrumb").find("a",href=re.compile(".*category/books/.*"))).text
        tag_book_rating=(soup_book.find("div",class_="col-sm-6 product_main").find("p", class_=re.compile("^star-rating.*")))["class"][1]
        tag_book_image_url=soup_book.find("div",class_="item active").find("img")["src"].replace("../../",URL_HOME+"/")

        dict_book={"product_page_url":url_book,\
                   "UPC":tag_book_upc,\
                   "title":tag_book_title,\
                   "price_including_tax":tag_book_price_with_tax,\
                   "price_excluding_tax":tag_book_price_wo_tax,\
                   "number_available":tag_book_stock,\
                   "product_description":tag_book_description,\
                   "category":tag_book_category,\
                   "review_rating":tag_book_rating,\
                   "image_url":tag_book_image_url}
        
        return dict_book


def create_csv(dict_book,cat_name):
    """
    Create csv file from dictionary
    Input: dict_book, cat_name
    Output:
    """  

    csv_name=str(cat_name)+".csv"
    path_csv=Path.cwd()/MAIN_DIR/cat_name/csv_name
    
    #Create csv file if it does not exist
    if not Path.is_file(path_csv):
        with path_csv.open("a", newline="", encoding="utf-8-sig") as csvfile: #Signature for encoding in Excel
            writer=csv.DictWriter(csvfile, dict_book, dialect="excel")
            writer.writeheader()

    #Fill csv file
    with path_csv.open("a", newline="", encoding="utf-8-sig") as csvfile: #Signature for encoding in Excel
        writer=csv.DictWriter(csvfile, dict_book, dialect="excel")
        writer.writerow(dict_book)
        
    return csv_name


#Step2 Scraping a category page searching for book links

def scrap_page_category(url_cat):
    """
    Create a directory named from the caterogy name,
    Scrap a category page searching for book links
    then scrap all books of the category
    Call functions: scrap_page_book, create_csv and save_images
    Input: url_cat
    Output:
    """
      
    #Create a directory named from the caterogy name
    response_url_cat=requests.get(url_cat)
        
    if not response_url_cat.ok:
        print("wrong url, cannot scrap this page category", url_cat)
        exit()
            
    else:       
        #Search for caterogy name
        soup_cat=bs(response_url_cat.text, "lxml")
        cat_name=(soup_cat.find("div",class_="page-header action").find("h1")).text
            
        #Create a directory named from the caterogy name
        path_category=Path.cwd()/MAIN_DIR/cat_name
        try:
            os.mkdir(path_category)
        except OSError as e:
            print(os.strerror(e.errno))
    
    #Scrap a category page searching for book links
    soup_cat_thisPage="index.html"
    urls_book=[]
    
    while url_cat!=None:
        response_url_cat=requests.get(url_cat)
        
        if not response_url_cat.ok:
            print("wrong url, cannot scrap this page category", url_cat)
            exit()
            
        else:
            soup_cat=bs(response_url_cat.text, "lxml")
            tag_cat=soup_cat.find("ol", class_="row").findAll("h3")
            
            for h3 in tag_cat:
                urls_book.append(h3.find("a")["href"].replace("../../../",URL_HOME+"/catalogue/"))
        
            #Test if next page
            test_tag_next=soup_cat.find("li",class_="next")
        
            if test_tag_next!=None:
                soup_cat_next=test_tag_next.find("a")["href"]
                url_cat=url_cat.replace(soup_cat_thisPage,soup_cat_next)
                soup_cat_thisPage=soup_cat_next
            else:
                url_cat=None
    
    #Scrap all books of the category
    for url_book in urls_book:
        #Scrap the page book
        dict_book=scrap_page_book(url_book)
        
        #Create the csv file
        csv_name=create_csv(dict_book,cat_name)
      
    #Save_images
    save_images(cat_name,csv_name)
        
    print("Web scraping done for",str(len(urls_book)),"books in the category",cat_name,"and images saved")
        

#Step3 Scraping the home page searching for category links and save images

def save_images(cat_name,csv_name):
    """
    Save book images
    Input: csv_name,cat_name
    Output:
    """
    
    #Read csvfile for image url and upc
    path_csv=Path.cwd()/MAIN_DIR/cat_name/csv_name
    
    with path_csv.open("r", newline="", encoding="utf-8-sig") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
    
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                image_name=row[1]+".jpg"
                url_image=row[9]

                #Get image
                response_url_images = requests.get(url_image)
                
                if not response_url_images.ok:
                    print("wrong url image,",image_name,"is not saved")

                #Open directory and save image
                else:
                    path_images=Path.cwd()/MAIN_DIR/cat_name/image_name
                    with path_images.open('wb') as jpgfile:   
                        jpgfile.write(response_url_images.content)


def scrap_page_home(url_home):
    """
    Scrap the home page searching for directory links
    then scrap all categories
    Call functions: scrap_page_category
    Input: url_home
    Output:
    """
    
    #Create a directory to save our web scraping
    try:
        os.mkdir(MAIN_DIR)
    except OSError as e:
        print(os.strerror(e.errno))
    
    #Scrap the home page searching for directory links
    response_url_home=requests.get(url_home)
    
    if not response_url_home.ok:
        print("wrong url, please review website url")
        exit()
    
    else:
        soup_home=bs(response_url_home.text, "lxml")
        tag_home=soup_home.find("ul", class_="nav nav-list").findAll("a")
        
        urls_cat=[]
        
        for a in tag_home:
            urls_cat.append(URL_HOME+"/"+a["href"]) 
        
        urls_cat.pop(0) #Remove the category Books from urls_cat
        
        print("There are",str(len(urls_cat)),"categories in this bookstore")
        
        #Scrap all categories
        for url_cat in urls_cat:
            scrap_page_category(url_cat)


#Main instructions to run
def main():
    """
    Main instructions to run
    Call function: scrap_page_home
    Input: URL_HOME
    Output:
    """
    
    scrap_page_home(URL_HOME)

    
if __name__=="__main__":
    main()


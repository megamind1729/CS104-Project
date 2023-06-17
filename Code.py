import sys
import argparse
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from functools import reduce

url_domain = ""
visited_link_set = set()
visited_link_level_set = set()
all_link_set = set()
sorted_links = {}
sorted_links_set = set()

extensions = ["css","htm","html","jpeg","jpg","js","mp4","pdf","php","png","webp","xml"]
attributes = ["href", "src"]

# Function to return a list of tags (eg: [<img src="...">, <a href="...">])
def get_links(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser",from_encoding="iso-8859-1")
        return soup.find_all(href=True) + soup.find_all(src=True)
    
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while requesting {url}:\n{e}\n")
        return []

#Function to get the webpage size
def get_webpage_size(url):
    try:
        response = requests.get(url)
        return len(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while requesting {url}:\n{e}\n")
        return None

#Function to get the file size
def get_file_size(url):
    try:
        response = requests.head(url)
        if 'Content-Length' in response.headers:
            return int(response.headers['Content-Length'])
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while requesting {url}:\n{e}\n")
        return None
        
def get_size(url):
	size1 = get_file_size(url)
	size2 = get_webpage_size(url)
	if(not size1 and not size2):
		return -1
	elif size2:
		return round(size2/1024,3)
	else:
		return round(size1/1024,3)		

#Function to get the domain of an url
def get_domain(url):
	parsed_url = urlparse(url)
	if parsed_url.netloc:
		return parsed_url.netloc
	else:
		return "Miscellaneous"

# Function to return a list with unique elements 
def unique_list(list1):
    unique_list1 = reduce(lambda re, x: re+[x] if x not in re else re, list1, [])
    return unique_list1

# Function to return whether 'url' has the domain 'domain' 
def is_internal_link(domain, url):
    parsed_url = urlparse(url)
    return parsed_url.netloc == domain

# Function to return file extension of url
def get_file_extension(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    if "." in path:
        if path.split(".")[-1].rstrip("\\") in extensions:
            return path.split(".")[-1].rstrip("\\")
        else:
            return "Miscellaneous"
    else:
        return "Miscellaneous"

def crawl(url, threshold):
    parsed_url = urlparse(url)
    global url_domain
    url_domain = parsed_url.netloc
    
    global visited_link_set
    global file_counts
    global sorted_links
    
    visited_link_set = set()
    file_counts = {}
    sorted_links = {}
    crawl_recursive(url,0,threshold,url_domain)
    return sorted_links

def crawl_recursive(url, recursion_level, threshold, url_domain):
    global visited_link_set
    global visited_link_level_set
    global sorted_links
    global sorted_links_set
    global all_link_set

    if threshold:
        if recursion_level >= threshold:
            return

    visited_link_set.add(url)	
    visited_link_level_set.add((url, recursion_level))
    
    links = get_links(url)  	# links - list of tags with href or src attributes

    for link in links:  			# link - tag with href or src attributes (eg: <img src="...">)
        for attr in attributes:
            attr_url = link.get(attr)                
            if attr_url:
                attr_url = urljoin(url, attr_url)

                if threshold:
                    condition = (attr_url,recursion_level) not in visited_link_level_set
                else:
                    condition = attr_url not in visited_link_set

                if is_internal_link(url_domain, attr_url) and condition:
                    visited_link_set.add(attr_url)
                    visited_link_level_set.add((attr_url,recursion_level+1))
                    crawl_recursive(attr_url,recursion_level+1,threshold,url_domain)

                file_extension = get_file_extension(attr_url)
                attr_url_domain = get_domain(attr_url)
                sorted_links.setdefault(recursion_level, {}).setdefault(file_extension, {}).setdefault(attr_url_domain, set()).add(attr_url)
                sorted_links_set.add((attr_url,attr_url_domain,file_extension,recursion_level))
                all_link_set.add((attr_url,file_extension,attr_url_domain))

def display(sorted_links,threshold,domain2,extension2,sort,file_size):
    
    total_files = sum(sum(sum(len(link_set) for link_set in domain_dict.values()) for domain_dict in ext_dict.values()) for ext_dict in sorted_links.values())
    domain2_count_total = sum(sum(len(domain_dict[domain2] if domain2 in domain_dict.keys() else {}) for domain_dict in ext_dict.values()) for ext_dict in sorted_links.values())
    
    if domain2:
        print(f"No. of files found with domain '{domain2}': {domain2_count_total}\n")

    for level in sorted(sorted_links.keys()):
        
        ext_dict = sorted_links[level]
        file_count_in_level = sum(sum(len(link_set) for link_set in domain_dict.values()) for domain_dict in ext_dict.values()) 
        domain2_count_level = sum(len(domain_dict[domain2] if domain2 in domain_dict.keys() else {}) for domain_dict in ext_dict.values())
        
        print(f"\nAt recursion level {level+1}")
        print(f"Total files found: {file_count_in_level}\n")
        if domain2:
            print(f"\tNo. of files found with domain '{domain2}': {domain2_count_level}\n")
            
        
        for ext in sorted(ext_dict.keys()):
            domain_dict = ext_dict[ext]
            file_count_in_ext = sum(len(link_set) for link_set in domain_dict.values())
            domain2_count_ext = len(domain_dict[domain2] if domain2 in domain_dict.keys() else {})  
        	
            print(f"\n\t{ext.capitalize()} : ")
            print(f"\tNo. of files found : {file_count_in_ext}\n")
            if domain2:
                print(f"\tNo. of files found with domain '{domain2}': {domain2_count_ext}\n")
        		
            if not domain2:
                for dom in sorted(domain_dict.keys()):
                    
                    link_set = sorted(domain_dict[dom])
                    file_count_in_domain = len(link_set)
                    
                    print(f"\n\t\tDomain : {dom}")
                    print(f"\t\tNo. of files found : {file_count_in_domain}\n")	
                    for i in link_set:
                        print(f"\t\t\t{i}")
                        if(file_size):
                            print(f"\t\t\tSize: {get_size(i)} KB")
            else:
                if domain2 in domain_dict.keys():
                    link_set = sorted(domain_dict[domain2])
                    file_count_in_domain = len(link_set)

                    for i in link_set:
                        print(f"\t\t\t{i} : Size : {get_size(i)} KB")
                        if(file_size):
                            print(f"\t\t\tSize: {get_size(i)} KB")
    
    print(f"\nNo of unique files visited: {len(visited_link_set)}")
    print(f"No of unique files found: {len(all_link_set)}")
    print(f"Total files found: {len(sorted_links_set)}")
'''
def display2(sorted_links_set, all_link_set, domain2, extension2, sort, file_size):
    if (domain2 is None):
         domain2 = list(set([i[1] for i in sorted_links_set]))
    if(extension2 is None):
         extension2 = list(set([i[2] for i in sorted_links_set])) 
    
    filtered_list = [i for i in all_link_set if (i[2] in extension2 and i[1] in domain2)]
    if sort is None:
        sorted_list = sorted(filtered_list, key= lambda i: (i[0],i[2],i[3]))
        for level in sorted(list({i[3] for i in filtered_list})):
             list1 = [i for i in filtered_list if i[3]==level]
             print(f"\nAt recursion level {level}")
             print(f"No of files found: {len(list1)}")
             for ext in sorted(list({i[2] for i in list1})):
                
                print(f"\n{ext.capitalize()}")
                for link in sorted(list({i[0] })):
                	print(f"{link}")

    elif sort == "domain":
        sorted_list = sorted(filtered_list, key= lambda i: (i[0],i[1],i[2],i[3]))
    elif sort == "file size":
        sorted_list = sorted(filtered_list, key= lambda i: (i[0],get_size(i[0]),i[2],i[3]))

    internal_file_count = len({i for i in all_link_set if i[2] == url_domain}) 
    print(f"\nFile Count: {len(filtered_list)}")
    print(f"\nNo of unique files visited: {len(visited_link_set)}")
    print(f"No of unique files found: {len(all_link_set)}")
    print(f"No of internal files: {internal_file_count}")
    print(f"No of external files: {len(all_link_set)-internal_file_count}")
    print(f"Total files found: {len(sorted_links_set)}")
'''
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="URL to crawl", required=True)
    parser.add_argument("-t", "--threshold", type=int, help="Threshold of recursiveness")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("-d", "--domain",nargs="*", help="URL domain needed")
    parser.add_argument("-e","--extension",nargs="*", help="Extension needed")
    parser.add_argument("-s","--sort", help="Sorts on given basis", action="store_true")
    parser.add_argument("-f","--file_size", help="Displays file size", action="store_true")
    
    args = parser.parse_args()    
    url = args.url
    org_stdout = sys.stdout
    threshold = args.threshold
    domain2 = args.domain
    extension2 = args.extension
    sort = args.sort
    file_size = args.file_size
    
    if threshold and threshold <= 0:
        print("Threshold must be greater than 0.")
        return
    
    if args.output:
        sys.stdout = open(args.output, "w")
    
    link_data = crawl(url, threshold)
    display(link_data,threshold,domain2,extension2,sort,file_size)

    if args.output:
        sys.stdout = org_stdout

if __name__ == "__main__":
    main()

import random
import json
import requests
from datetime import datetime
import re
import time

def fetch_version_data(component, version):
    if version is None:
        url = f'https://releasetrain.io/api/c/name/{component}'
    else:
        url = f'https://releasetrain.io/api/c/name/{component}/{version}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"Failed to fetch data for {component} {version}: {err}")
    except Exception as err:
        print(f"An error occurred while fetching data for {component} {version}: {err}")

def fetch_recent_posts(limit=1000, retries=5, backoff_factor=0.5):
    url = f'https://www.reddit.com/r/all/new/.json?limit={limit}'
    headers = {'User-Agent': 'Mozilla/5.0'}

    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()['data']['children']
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:  # Too Many Requests
                if i < retries - 1:  # Check if we have retries left
                    sleep_time = 180 if i == retries - 2 else backoff_factor * (2 ** i)
                    print(f"Rate limit exceeded. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print(f"Rate limit exceeded. Waiting for 3 minutes before retrying...")
                    time.sleep(180)
            else:
                print(f"Failed to fetch recent posts: {err}")
                break
        except Exception as err:
            print(f"An error occurred while fetching recent posts: {err}")
            break
    return []

def fetch_hot_posts(subreddit, limit=1000, retries=5, backoff_factor=0.5):
    url = f'https://www.reddit.com/r/{subreddit}/hot/.json?limit={limit}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            posts = response.json()['data']['children']
            return posts
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:  # Too Many Requests
                if i < retries - 1:  # Check if we have retries left
                    sleep_time = 180 if i == retries - 2 else backoff_factor * (2 ** i)
                    print(f"Rate limit exceeded. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print(f"Rate limit exceeded. Waiting for 3 minutes before retrying...")
                    time.sleep(180)
            else:
                print(f"Failed to fetch hot posts for subreddit {subreddit}: {err}")
                break
        except Exception as err:
            print(f"An error occurred while fetching hot posts for subreddit {subreddit}: {err}")
            break
    return []

def search_by_keywords(posts, keywords):
    for post in posts:
        print(post['data']['title'].lower())
    return [post for post in posts if any(keyword.lower() in post['data']['title'].lower() for keyword in keywords)]

def check_for_version_numbers(post_title):
    version_pattern = r'\b(?:v)?(\d+)(?:\.(\d+))?(?:\.(\d+))?\b'
    matches = re.findall(version_pattern, post_title)
    
    versions = []
    for match in matches:
        major = match[0] if match[0] else '0'
        minor = match[1] if match[1] else '0'
        patch = match[2] if match[2] else '0'
        version = f"{major}.{minor}.{patch}"
        versions.append(version)
    
    return versions

def print_posts_and_enrich_versions(posts):
    for post in posts:
        data = post['data']
        versions = check_for_version_numbers(data['title'])
        version_data = fetch_version_data(data['subreddit'], None)

        iteration_limit = 50
        iteration_count = 0

        for version_detail in version_data[data['subreddit']]:
            
            if iteration_count >= iteration_limit:
                break

            iteration_count += 1

            if 'user_post_reddit' not in version_detail:
                version_detail['user_post_reddit'] = {}

            if data['id'] not in version_detail['user_post_reddit']:
                version_detail['user_post_reddit'][data['id']] = {
                    'title': data['title'],
                    'subreddit': data['subreddit'],
                    'score': data['score'],
                    'versionList': versions,
                    'post_id': data['id'],
                    'created_utc': datetime.fromtimestamp(data['created_utc']).isoformat(),
                    'url': f"https://reddit.com{data['permalink']}",
                    'author': data['author'],
                    'num_comments': data['num_comments'],
                    'upvote_ratio': data['upvote_ratio'],
                    'awards': data.get('all_awardings', []),
                }
                update_version(version_detail['_id'], version_detail)

def update_version(version_id, update_data):  
    print(json.dumps(update_data, indent=4))  # Print the update data for debugging
    url = f'https://releasetrain.io/api/v/{version_id}'
    try:
        response = requests.put(url, json=update_data)
        print(f"Status Code: {response.status_code}")
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as err:
        return f"Failed to update data: HTTP error occurred: {err.response.status_code} - {err.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Failed to update data: A network-related error occurred: {e}"
    except Exception as e:
        return f"Failed to update data: An unexpected error occurred: {e}"

def fetch_os_components():
    url = 'https://releasetrain.io/api/v'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()  # Parse the response as JSON
        print(type(data))
        if isinstance(data, list) and all(isinstance(item, dict) and 'versionProductName' in item for item in data):
            components = list(set(item['versionProductName'].strip().lower() for item in data if item['versionProductName'].strip()))  # Ensure unique, non-empty component names in lower case
            random.shuffle(components)  # Shuffle the list to return in random order
            return components
        else:
            print("Unexpected response format")
            return []
    except requests.exceptions.HTTPError as err:
        print(f"Failed to fetch OS components: {err}")
        return []
    except Exception as err:
        print(f"An error occurred while fetching OS components: {err}")
        return []

components = fetch_os_components()
print(components)

if components:
    for component in components:
        if component.isdigit():
            print(f"Skipping invalid component: {component}")
            continue

        print(f"Processing component: {component}")

        # Fetch posts from specific subreddit
        subreddit_posts = fetch_hot_posts(component, limit=1000)
        if subreddit_posts:
            print(f"Found {len(subreddit_posts)} posts in subreddit {component}")
            print_posts_and_enrich_versions(subreddit_posts)
        else:
            print(f"No posts found in subreddit {component}")
else:
    print("No components to process.")
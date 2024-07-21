import pymongo
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
import requests
import json
from datetime import datetime
import time
import sys
from bson import ObjectId

# pip3 install -U scikit-learn scipy matplotlib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

def default(o):
    if isinstance(o, ObjectId):
        return str(o)
    raise TypeError(f'Object of type {o.__class__.__name__} is not JSON serializable')

categories_component = {
    "gpt": ["GPT", "GPT model", "OpenAI", "LLM", "GPT-2", "GPT-3", "GPT-4", "NLP", "ChatGPT", "Transformer", "Language Model"],
    "bitcoin": ["bitcoin", "ethereum", "crypto", "Cryptocurrency", "Blockchain", "Cryptographic", "Mining", "Wallet", "DeFi", "Altcoin"],
    "browser": ["browser", "Chrome", "Firefox", "Edge", "Safari", "Opera", "Chromium", "Brave", "Vivaldi", "Web Browser", "Extensions"],
    "database": ["database", "SQL", "NOSQL", "key-value", "store", "MongoDB", "PostgreSQL", "Cassandra", "MySQL", "RDBMS", "DBMS"],
    "os": ["os", "ios", "android", "red hat", "windows", "linux", "Ubuntu", "macOS", "CentOS", "kernel", "linux-dist", "apple", "phone", "operating system"],
    "server": ["server", "jenkins", "nginx", "Apache", "Tomcat", "Web Server", "Application Server", "HTTP Server"],
    "ide": ["ide", "vim", "VSCode", "PyCharm", "Eclipse", "command line", "shell", "command", "editor", "Integrated Development Environment"],
    "api": ["api", "swagger", "REST", "GraphQL", "SOAP", "Application Programming Interface", "Endpoint", "API Gateway"],
    "framework": ["framework", "react", "vue", "Angular", "Django", "Spring", "Rails", "Laravel", "Frameworks"],
    "library": ["library", "jQuery", "React Router", "Redux", "Library", "Toolkit"],
    "language": ["language", "python", "JavaScript", "Java", "C#", "Ruby", "script", "programming language", "coding language", "scripting language"],
    "versioning": ["versioning", "version management", "Git", "SVN", "Mercurial", "Version Control", "GitHub", "Branching", "Merging"],
    "app": ["app", "wordpress", "Drupal", "Joomla", "Application", "Web App", "Mobile App"],
    "repository": ["repository", "repositories", "package", "package manager", "package", "repo", "version control", "package", "npm", "NuGet", "Maven", "PyPI", "CRAN", "GitHub", "GitLab", "Bitbucket", "dependency"],
    "cloud": ["cloud", "aws", "azure", "cloud computing", "Lambda", "Azure Functions", "App Engine", "aws", "GCP", "Cloud Services"],
    "containerization": ["container", "docker", "kubernetes", "Docker Swarm", "OpenShift", "distributing", "Container Orchestration", "Containers"],
    "testing": ["testing", "unit testing", "integration testing", "test automation", "Selenium", "JUnit", "pytest", "TDD", "Test Driven Development"],
    "mobile": ["mobile", "mobile app", "React Native", "Swift", "Kotlin", "iOS", "Android", "Mobile Development"],
    "web": ["web", "html", "css", "javascript", "web development", "Vue.js", "Node.js", "Bootstrap", "Web Design", "Frontend", "Backend"],
    "data": ["data", "big data", "data analytics", "data science", "Hadoop", "Spark", "Pandas", "Data Engineering", "Data Analysis"],
    "agile": ["agile", "scrum", "kanban", "agile methodology", "Jira", "Trello", "Scrum Master", "Agile Development"],
    "devops": ["devops", "continuous integration", "continuous deployment", "devops practices", "Jenkins Pipeline", "Ansible", "Docker Compose", "CI/CD", "Infrastructure as Code"],
    "firmware": ["firmware", "firmwares", "embedded", "flash"]
}

categories_security = {
    "security": [
        "cve", "vpn", "firewall", "encryption", 
        "cybersecurity", "malware", "antivirus", "intrusion", 
        "detection", "prevention", "zeroday", "phishing", "ddos", 
        "ransomware", "spyware", "trojan", "worm", "backdoor", 
        "penetration", "vulnerability", "assessment", "patch"
    ]
}

categories_breaking = {
    "breaking": [
        "400", "401", "402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", "415", "416", "417", "418", "421", "422", "423", "424", "425", "426", "428", "429", "431", "451", 
        "500", "501", "502", "503", "504", "505", "506", "507", "508", "510", "511", 
        "broken", "breaking", "error", "exception", "privacy", "legal", "terms", "conditions", "hipaa", "password", 
        "bluetooth", "authentication", "authorization", "compliance", 
        "breach", "leak", "confidentiality", "integrity", "bluetooth",
        "availability", "audit", "gdpr", "ccpa", "sox", "pci", "performance", "slow", "wifi", "restart", "sign in", "glitch", "weird"
    ]
}

def prepare_training_data(categories):
    training_data = []
    training_labels = []
    for category, data in categories.items():
        training_data.extend(data)
        training_labels.extend([category.upper()] * len(data))
    return training_data, training_labels

# Prepare separate training data for components, security, and breaking
train_data_component, train_labels_component = prepare_training_data(categories_component)
train_data_security, train_labels_security = prepare_training_data(categories_security)
train_data_breaking, train_labels_breaking = prepare_training_data(categories_breaking)

# Create Logistic Regression models
model_component = make_pipeline(CountVectorizer(), LogisticRegression())
model_security = make_pipeline(CountVectorizer(), LogisticRegression())
model_breaking = make_pipeline(CountVectorizer(), LogisticRegression())

client = pymongo.MongoClient("mongodb+srv://dev:8Lhs45R0m3SzRREQ@cluster0-rzt9l.mongodb.net/test?retryWrites=true&w=majority")
database = client.releasetrain
collection = database.versions

result = collection.find({'user_post_reddit': {'$exists': True}}).sort('_id', -1).limit(1000)
result = list(result)
TOTAL_VERSIONS = len(result)
print(TOTAL_VERSIONS)

count = 0
for version in result:

    if "_id" not in version or version["_id"] is None or str(version["_id"]) == "":
        count = count + 1
        print('NOK', version)
        continue

    try:
        version["versionSearchTags"] = [item for item in version["versionSearchTags"] if item != "BITCOIN"]

        # Create versionSummary
        version["versionSummary"] = f"{version['versionProductName']} {version['versionReleaseChannel']} {version['versionProductLicense']} {version['versionProductBrand']} {version['versionReleaseNotes']} {version['versionReleaseComments']} {' '.join(version['versionSearchTags'])}"
        version["versionSummary"] = ' '.join(sorted(set(version["versionSummary"].split()), key=version["versionSummary"].split().index))

        # Create versionSummaryReddit
        version["versionSummaryReddit"] = " ".join(f" {sub_object['title']}" for sub_object in version["user_post_reddit"].values())

        # Classification
        test_data = [version["versionSummary"]]
        test_data_reddit = [version["versionSummaryReddit"]]

        # Make predictions for versionSummary and versionSummaryReddit using Logistic Regression
        prediction_component = model_component.fit(train_data_component, train_labels_component).predict(test_data)[0]
        prediction_reddit_component = model_component.fit(train_data_component, train_labels_component).predict(test_data_reddit)[0]

        # Determine if security or breaking
        def check_category(pred, categories):
            return any(category in pred.lower() for category in categories)

        # Initialize counts
        security_count = 0
        breaking_count = 0
        non_security_count = 0
        non_breaking_count = 0

        predicted_component_type_counts = {}

        for post in version["user_post_reddit"].values():
            is_security = check_category(post["title"], categories_security['security'])
            is_breaking = check_category(post["title"], categories_breaking['breaking'])

            post["isSecurity"] = is_security
            post["isBreaking"] = is_breaking

            # Update counts
            if is_security:
                security_count += 1
            else:
                non_security_count += 1
            
            if is_breaking:
                breaking_count += 1
            else:
                non_breaking_count += 1

            # Predict component type for each Reddit post
            test_data_reddit_post = [post["title"]]
            prediction_reddit_post = model_component.fit(train_data_component, train_labels_component).predict(test_data_reddit_post)[0]           

            if "predictedComponentType" not in post:
                post["predictedComponentType"] = []

            if prediction_reddit_post not in version["versionSearchTags"]:
                version["versionSearchTags"].append(prediction_reddit_post)

            if prediction_reddit_post not in post["predictedComponentType"]:
                post["predictedComponentType"].append(prediction_reddit_post)
            
            if prediction_reddit_post in predicted_component_type_counts:
                predicted_component_type_counts[prediction_reddit_post] += 1
            else:
                predicted_component_type_counts[prediction_reddit_post] = 1

        # Calculate percentages
        total_posts = len(version["user_post_reddit"])
        security_percentage = (security_count / total_posts) * 100 if total_posts > 0 else 0
        breaking_percentage = (breaking_count / total_posts) * 100 if total_posts > 0 else 0

        # Add counts and percentages to version object
        version["securityRedditPostCount"] = security_count
        version["breakingRedditPostCount"] = breaking_count
        version["nonSecurityRedditPostCount"] = non_security_count
        version["nonBreakingRedditPostCount"] = non_breaking_count
        version["securityRedditPostPercentage"] = f"{security_percentage:.2f}%"
        version["breakingRedditPostPercentage"] = f"{breaking_percentage:.2f}%"
        version["predictedRedditComponent"] = predicted_component_type_counts

        # Print or use the predictions for versionSummary
        version["versionPredictedComponentType"] = prediction_component
        if prediction_component not in version["versionSearchTags"]:
            version["versionSearchTags"].append(prediction_component)

        # Update version
        version["_id"] = str(version["_id"])
        version["versionTimestampLastUpdate"] = datetime.now().isoformat()

        # Validate ID length
        if len(str(version["_id"])) != 24:
            count = count + 1
            continue

        del version["versionSummary"]
        del version["versionSummaryReddit"]

        # upload
        # print(json.dumps(version, indent=4))

        url = 'https://releasetrain.io/api/v/' + version["_id"]

        response = requests.put(url, data=json.dumps(version), headers={'Content-Type': 'application/json'})

        percentage = (count / TOTAL_VERSIONS) * 100
        percentage = "{:.2f}".format(percentage)
        print("Status " + str(percentage) + "% :: " + str(response.text) + " ( " + str(count) + " / " + str(TOTAL_VERSIONS) + " )")

    except TypeError as e:
        print("TypeError occurred:", e)
        sys.exit(1)
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)
    finally:
        count = count + 1
        continue
import sqlite3
import json

def search_products(keywords):
    # Connect to the SQLite database
    conn = sqlite3.connect(r'C:\Users\Dell\Desktop\Slay-AI\fashion_data.db')
    cursor = conn.cursor()

    # SQL query using the LIKE operator
    query = """
    SELECT uniq_id, product_name, description, brand, image, retail_price, discounted_price
    FROM fashion_sql
    WHERE
    """
    
    # Wildcard matching for the keyword
    keywords_list = keywords.split()
    
    # Add conditions for each keyword
    conditions = []
    for keyword in keywords_list:
        condition = "(product_name LIKE ? OR description LIKE ?)"
        conditions.append(condition)

    query += " AND ".join(conditions)

    params = []
    for keyword in keywords_list:
        wildcard_keyword = f"%{keyword}%"
        params.extend([wildcard_keyword, wildcard_keyword])

    # Execute the query with the keyword
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    # Close the connection
    conn.close()

    # Convert results to a list of dictionaries
    products = []
    for result in results:
        product = {
            "uniq_id": result[0],
            "product_name": result[1],
            "product_image": json.loads(result[4])[0],
            "brand": result[3],
            "retail_price": result[5],
            "discounted_price": result[6]
        }
        products.append(product)

    # Convert the list to a JSON string
    return json.dumps(products, indent=4)



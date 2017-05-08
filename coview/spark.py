import itertools
from pyspark import SparkContext

sc = SparkContext("spark://spark-master:7077", "PopularItems")

data = sc.textFile("/tmp/data/access.log", 2)  # each worker loads a piece of the data file


# helper function to generate co-views
def createUserCarTupleList(users):
    tupleList = []
    for i, j in itertools.combinations(sorted(users[1]), 2):
        tupleList.append((users[0], (i, j)))
    return tupleList


# 1. Read in data user-car as K-V pairs from log file
user = data.map(lambda line: line.split("\t"))  # tell each worker to split each line of it's partition

# 2. Group data by user and car ids
userList = user.groupByKey().map(lambda x: (x[0], set(x[1])))

# 3. group the user's all co-views using the helper function
userCarPairs = userList.flatMap(createUserCarTupleList(userList))

# 4 only keep the cars in the tuples list
itemPairUserList = userCarPairs.map(lambda pair: (pair[1], 1))
itemPairUserList = itemPairUserList.distinct()

# 5.enumerate the occurences
itemPairCount = itemPairUserList.map(lambda x: (x[0], 1)).reduceByKey(lambda x, y: int(x) + int(y))

# 6, Filter out unpopular cars, which are viewed by fewer than 3 people
filteredCount = itemPairCount.filter(lambda x: x[1] >= 3)

output = filteredCount.collect()  # bring the data back to the master node so we can print it out
for tuple in output:
    print(tuple)
print("Popular items done")
sc.stop()

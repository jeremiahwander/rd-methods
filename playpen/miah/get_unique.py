filepath = "/mnt/data/filters.txt"

unique = set()
linecount = 0

# iterate over every line in the file, add values to set
with open(filepath, "r") as fp:
    while line := fp.readline().strip():
        linecount += 1
        unique.add(line)

        if linecount % 1000 == 0:
            print(f"linecount is {linecount}")

print(unique)

# filepath = "/mnt/data/RGP_microsoft_output_111422.vcf.bgz"

# # iterate over gzipped tsv file
# import gzip

# linecount = 0
# unique = set()
# with gzip.open(filepath, "rt") as fp:
#     while line := fp.readline().strip():
#         if line.startswith("#"):
#             continue
#         linecount += 1
#         filter_line = line.split("\t", 7)[6]
#         #        print(filter_line)
#         unique.add(filter_line)
#         if linecount % 1000 == 0:
#             print(f"linecount is {linecount}")

# print(unique)

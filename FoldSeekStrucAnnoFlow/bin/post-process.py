# I think I want to make this nextflow seperate things but I'll plan what I want to do here


# 1. I want to compare my results to Interpro scan results. That means I need to figure out the best way to do that.
# 2. To start I need to address the other issue with the pipeline. It currently has a lot of bloat with the AF_ID etc thats not needed. I can make a few more dummy files in the process
# 3. That can be done but I think I have enough to create a new nextflow pipeline that handles post processing.

#   1. Take an input of the important file names, the foldseek results, both cath and non-cath then the interproscan results.
#   2. Next I need to specifcally match the results to the same
# 3. This won't be perfect as the Interpro results and the input data are going to sturuggle to find a match. I think it's fair to say that the
# Interpro results will be a gene_id and therefore I can match the gene_id and find the corresponding gene. It'll be good to add an inital check

#  4. When I have them matched up. I need to see if the foldseek results are the same as the interpro results. This can onlt be done with CATH and PFAM currently
# 5. Can I do anything with the AFDB results. Can I also look at the top 5 for each result that pass too. I think I can use vector comparison instead of pure string comparison to see if the results are similar.
#  but I think I can also do a string comparison and then a vector comparison to see if the results are similar.

# 6. Then I can generate some plots to show the results.

# 7 . One of the issues is is that I'm only looking at ones which have an Interpro match. I need to find ones which don't have any Interpro match or no PFAM or CATH match


# So The python files I need

# 1. A script which matches the file names from the results to the interproscan ids

# This is a file used only for utils, should be included, not run directly.


# Function checks if the command returns just one line
# Params:
#     $1 - string with command
#     $2 - expected number of elements
#     $3 - number of additional lines
#     $4 - singular form of the searched thing
#     $5 - command to remove additional entries 
function should_be {

    #echo $1
    OUT=$(eval $1 | wc -l)
    #echo $OUT
    
    if [[ $OUT -eq $2+$3 ]]; then
        echo "Found $2 $4(s)"
    else
        entries_found=`expr $OUT - $3`
        echo ""
        echo "Found a problem, there should be $2 $4, but found $entries_found."
        echo ""
        echo "You can remove the additional entries using:"
        echo $5
        echo ""
        exit
    fi
    
}



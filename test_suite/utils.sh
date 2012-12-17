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

# Function prints warning information
# PARAMS:
#     $1 - name of the service
#     $2 - additional line to print
#     $3 - additional line to print
#     $4 - additional line to print
function print_warning {

    echo 
    echo "      WARNING, THIS TEST SCRIPT WILL BE CREATING AND DELETING DATA"
    echo "             YOU SHOULD RUN IT ON A SPECIAL TEST ACCOUNT"
    echo "          THIS ACCOUNT SHOULD HAVE ACCESS TO THE $1 SERVICE"
    echo
    echo $2
    echo
    echo $3
    echo
    echo $4
    echo
    
    read -p "Press any key to proceed..."

}


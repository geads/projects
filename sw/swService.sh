#!/bin/bash

diff () {
        printf '%s' $(( $(date -u -d"$TARGET" +%s) -
                        $(date -u -d"$CURRENT" +%s)))
}

DBFILE=$1
TMPFILE=/tmp/sw2
HTTPBRDPASS=/tmp/httpBrdPass
PARSEDBRDPASS=/tmp/parsedBrdPass
PWDFILE=/etc/swd/password

USERNAME=$(cat $PWDFILE | awk '{print $1}')
PWD=$(cat $PWDFILE | awk '{print $2}')

while true; do

    python /etc/swd/pyRecvMail.py $DBFILE $USERNAME $PWD

    #If the DB is empty, sleep for a minute then try again
    nlines=`wc -l $DBFILE | awk '{print $1}'`
    if [ $nlines -eq 0 ]; then
        sleep 60
        python /etc/swd/pyRecvMail.py $DBFILE $USERNAME $PWD
    fi

    MIN=300
    while read LINE ; do
        DATE=$(echo $LINE | awk -F "|" '{print $4}')
        DATE=$(date -d"$DATE -1 days" +%Y-%m-%d)
        TIME=$(echo $LINE | awk -F "|" '{print $5}')
        IATA=$(echo $LINE | awk -F "|" '{print $6}')

        sleep 1

        CURRENT=$(TZ='America/Chicago' date)
        TARGET=$(dateconv $(date -d"$DATE $TIME" +%Y-%m-%dT%R:%S) --from-zone iata:$IATA --zone UTC)

        if [ $(diff) -lt $MIN ]; then
            MIN=$(diff)
        fi

        echo "Current: $CURRENT"
        echo "Target:  $TARGET (UTC)"
        echo "Seconds left: $(diff)"
    done < $1

    #If there are no checkins in the next 5 minutes, sleep
    if [ $MIN -ge 300 ]; then
        sleep 300
    fi

    N=0
    while read LINE ; do
        N=$((N+1))

        FIRSTNAME=$(echo $LINE | awk -F "|" '{print $1}')
        LASTNAME=$(echo $LINE | awk -F "|" '{print $2}')
        CONFNUM=$(echo $LINE | awk -F "|" '{print $3}')
        DATE=$(echo $LINE | awk -F "|" '{print $4}')
        DATE=$(date -d"$DATE -1 days" +%Y-%m-%d)
        TIME=$(echo $LINE | awk -F "|" '{print $5}')
        IATA=$(echo $LINE | awk -F "|" '{print $6}')
        EMAIL=$(echo $LINE | awk -F "|" '{print $7}')
        NUM_PASSENGERS=$(echo $LINE | awk -F "|" '{print $8}')

        sleep 1

        CURRENT=$(TZ='America/Chicago' date)
        #TARGET=$(TZ='America/Chicago' date -d"$DATE $TIME")
        TARGET=$(dateconv $(date -d"$DATE $TIME" +%Y-%m-%dT%R:%S) --from-zone iata:$IATA --zone UTC)

        echo "Current: $CURRENT"
        echo "Target:  $TARGET (UTC)"
        echo "Seconds left: $(diff)"

        # Don't check-in until the time is right
        if [ $(diff) -gt 0 ]; then
            continue
        fi

        # Delete the db entry if the flight's already departed
        if [ $(diff) -lt -86400 ]; then
            echo "Deleting entry: $LINE"
            sed ${N}d $DBFILE > $TMPFILE
            mv $TMPFILE $DBFILE
        fi

        python /etc/swd/swCheckIn.py $FIRSTNAME $LASTNAME $CONFNUM $NUM_PASSENGERS > $HTTPBRDPASS
        if [ ! $? -eq 0 ]; then
            continue
        fi

        #parse HTTP for boarding positions
        BRDGROUP=($(sed -rn 's/.*class.*group.+alt=\"([A-Z])\".*/\1/p' $HTTPBRDPASS))
        BRDPOS=($(sed -rn 's/.*class.*position.+alt=\"([0-9])\".+alt=\"([0-9])\".*/\1\2/p' $HTTPBRDPASS))
	NUMTIX=${#BRDGROUP[@]}

        if [ $NUMTIX -eq 0 ]; then
            BRDGROUP=($(sed -rn 's/.*boarding_group.+>([A-Z])<.*/\1/p' $HTTPBRDPASS))
            BRDPOS=($(sed -rn 's/.*boarding_position.*>([0-9])([0-9])<.*/\1\2/p' $HTTPBRDPASS))
            NUMTIX=${#BRDGROUP[@]}
	fi

        echo "Num tickets: $NUMTIX"
        echo "Boarding group: $BRDGROUP"
        echo "Boarding position: $BRDPOS"

        rm -f $PARSEDBRDPASS
        for i in $(seq 0 $((NUMTIX-1)) )
        do
            echo "Boarding position for ticket #$i: ${BRDGROUP[$i]}${BRDPOS[$i]}" >> $PARSEDBRDPASS
        done

        python /etc/swd/pySendMail.py $PARSEDBRDPASS $USERNAME $PWD $EMAIL

        sed ${N}d $DBFILE > $TMPFILE
        mv $TMPFILE $DBFILE
        break
    done < $1
done

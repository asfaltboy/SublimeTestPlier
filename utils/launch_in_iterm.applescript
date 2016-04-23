set test_cmd to system attribute "TEST_CMD"
 
tell application "iTerm"
    activate
    (* set t to (make new terminal) *)

    -- make a new terminal
    -- set myterm to (current terminal)
    set myterm to (make new terminal)
    
    -- talk to the new terminal
    tell myterm

        -- make a new session
        set mysession to launch session "Default"
        -- set mysession to (make new session at the end of sessions)
        -- select mysession

        -- talk to the session
        tell mysession

            -- execute a command
            -- exec command test_cmd
            write text test_cmd
        end tell -- we are done talking to the session
    end tell
end tell
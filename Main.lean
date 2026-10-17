import LeanPose.Protocol

open Lean LeanPose

private def emit (input : String) (batch : Bool := false) : IO UInt32 := do
  let stdout ← IO.getStdout
  match (if batch then handleBatchRequest input else handleRequest input) with
  | .ok response => stdout.putStrLn response.compress; return 0
  | .error message =>
      stdout.putStrLn (Json.mkObj [("error", toJson message)]).compress
      return 1

private partial def jsonLines (hadError : Bool := false) : IO UInt32 := do
  let line ← (← IO.getStdin).getLine
  if line.isEmpty then return if hadError then 1 else 0
  let code ← emit line
  jsonLines (hadError || code != 0)

/-- A single file or stdin request; --jsonl accepts one independent request per line. -/
def main (args : List String) : IO UInt32 := do
  try
    match args with
    | ["--jsonl"] => jsonLines
    | ["--batch"] => emit (← (← IO.getStdin).readToEnd) true
    | ["--help"] =>
        (← IO.getStdout).putStrLn "Usage: leanpose [request.json | --jsonl | --batch | --help]\nWithout arguments, read one JSON request from stdin."
        return 0
    | [] => emit (← (← IO.getStdin).readToEnd)
    | [path] => emit (← IO.FS.readFile path)
    | _ =>
        (← IO.getStderr).putStrLn "Usage: leanpose [request.json | --jsonl | --batch | --help]"
        return 2
  catch error =>
    (← IO.getStderr).putStrLn s!"leanpose: {error}"
    return 2

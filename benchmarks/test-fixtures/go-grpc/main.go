package main

import (
	"fmt"
	"log"
	"net"

	"google.golang.org/grpc"
	pb "github.com/example/grpc/proto"
)

type Server struct {
	pb.UnimplementedGreeterServer
}

func (s *Server) SayHello(req *pb.HelloRequest) string {
	return fmt.Sprintf("Hello, %s!", req.Name)
}

func main() {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	s := grpc.NewServer()
	pb.RegisterGreeterServer(s, &Server{})

	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
